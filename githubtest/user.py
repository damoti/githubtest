import json
import asyncio
import github3
import requests
from github3.session import AppBearerTokenAuth
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from pyotp import TOTP
from slugify import slugify

from githubtest.state import GitHubTestState
from githubtest.utils import get_form_data


class RunInExecutorWrapper:

    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, name):
        if name.startswith('async_'):
            name = name[len('async_'):]
            if name.startswith('first_'):
                name = name[len('first_'):]
                return self.wrap(next, getattr(self.obj, name)(), None)
            return self.wrap(getattr(self.obj, name))
        return getattr(self.obj, name)

    @classmethod
    def wrap(cls, *args, **kwargs):
        async def _wrap(*sub_args, **sub_kwargs):
            result = await asyncio.get_running_loop().run_in_executor(
                None, *args, *sub_args, **kwargs, **sub_kwargs
            )
            return cls(result)
        return _wrap


class GitHubTestUser:

    HOST = "https://github.com/"

    def __init__(self, manifest: dict, session: requests.Session):
        self.app_name = manifest['name']
        self.app_id = slugify(self.app_name)
        self.manifest = manifest
        self.session = session
        self._user = github3.GitHub()
        self._app = github3.GitHub()
        self.state = GitHubTestState(self.app_id)

    @classmethod
    def connect(cls, manifest, secret, oauth, username, password) -> 'GitHub':
        gh = cls(manifest, requests.Session())
        print('gh.login')
        gh.login(secret, username, password)
        print('gh._user.login')
        gh._user.login(token=oauth)
        return gh

    def disconnect(self):
        if self.session:
            self.session.close()
        if self._user.session:
            self._user.session.close()
        if self._app.session:
            self._app.session.close()

    def get(self, url):
        return self.session.get(self.HOST + url)

    def post(self, url, *args, **kwargs):
        return self.session.post(self.HOST + url, *args, **kwargs)

    def login(self, secret, username, password):
        r = self.get("session")
        data = get_form_data(r.content, action="/session")
        data['login'] = username
        data['password'] = password
        r = self.post("session", data=data)
        data = get_form_data(r.content, action="/sessions/two-factor")
        data['otp'] = TOTP(secret).now()
        r = self.post("sessions/two-factor", data=data)

    def get_user_api(self):
        return RunInExecutorWrapper(self._user)

    def ensure_app(self):
        if not self.get_app_data():
            self.create_app()

    def get_app_api(self):
        app = self.state.get('app')
        if app:
            if not isinstance(self._app.session.auth, AppBearerTokenAuth):
                self._app.login_as_app(app['pem'].encode(), app['id'])
            return self._app
        raise ValueError('App state not found.')

    def get_app_data(self) -> dict:
        r = self.get(f"settings/apps/{self.app_id}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html5lib')
            form = soup.find('form', class_='edit_integration')
            data = {}
            for key, value in get_form_data(form=form).items():
                if key.startswith('integration'):
                    name = key[len('integration')+1:key.find(']')]+key[key.find(']')+1:]
                    data[name] = value
            return data
        return {}

    def create_app(self):
        app = json.dumps(self.manifest)
        r = self.post("settings/apps/new", data={'manifest': app})

        soup = BeautifulSoup(r.content, 'html5lib')
        error = soup.find('div', class_='manifest-errors')
        if error:
            raise ValueError([e.text.strip() for e in error.parent.find_all('strong', class_='text-red')])

        data = get_form_data(r.content, id='new_integration_manifest')
        r = self.post("settings/apps", data=data)
        soup = BeautifulSoup(r.content, 'html5lib')
        errors = soup.find_all('dd', class_='error')
        if errors:
            raise ValueError([e.text.strip() for e in errors])
        redirect = soup.find('a', id="redirect")['href']
        code = parse_qs(urlparse(redirect).query)['code'][0]
        r = self.session.post(f"https://api.github.com/app-manifests/{code}/conversions", headers={
            'Accept': 'application/vnd.github.fury-preview+json'
        })
        self.state['app'] = r.json()

    def delete_app(self):
        r = self.get(f"settings/apps/{self.app_id}/advanced")
        soup = BeautifulSoup(r.content, 'html5lib')
        form = soup.find('input', id='confirm-delete-app').parent.parent
        data = get_form_data(form=form)
        data['verify'] = self.app_name
        r = self.post(f"settings/apps/{self.app_id}", data=data)
        self.state['app'] = None

    def ensure_install(self):
        api = self.get_app_api()
        if not next(api.app_installations(), None):
            self.install_app()

    def install_app(self):
        r = self.get(f"apps/{self.app_id}/installations/new")
        data = get_form_data(r.content, class_='js-integrations-install-form')
        data['install_target'] = 'all'
        r = self.post(f"apps/{self.app_id}/installations", data=data)
