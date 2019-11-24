import json
import github3
import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from pyotp import TOTP

from githubtest.state import GitHubTestState
from githubtest.utils import get_external_ip, get_form_data


class GitHubTestUser:

    HOST = "https://github.com/"

    def __init__(self, app_name: str, external_ip: str, session: requests.Session):
        self.app_name = app_name+' '+external_ip
        self.app_id = self.app_name.lower().replace(' ', '-').replace('.', '-')
        self.external_ip = external_ip
        self.session = session
        self.user_api = github3.GitHub()
        self.state = GitHubTestState()

    @classmethod
    def connect(cls, app_name, secret, username, password) -> 'GitHub':
        gh = cls(app_name, get_external_ip(), requests.Session())
        gh.login(secret, username, password)
        gh.user_api.login(username, password, two_factor_callback=TOTP(secret).now)
        return gh

    def login(self, secret, username, password):
        r = self.get("session")
        data = get_form_data(r.content, action="/session")
        data['login'] = username
        data['password'] = password
        r = self.post("session", data=data)
        data = get_form_data(r.content, action="/sessions/two-factor")
        data['otp'] = TOTP(secret).now()
        r = self.post("sessions/two-factor", data=data)

    def get(self, url):
        return self.session.get(self.HOST + url)

    def post(self, url, *args, **kwargs):
        return self.session.post(self.HOST + url, *args, **kwargs)

    def app_exists(self):
        r = self.get(f"settings/apps/{self.app_id}")
        return r.status_code == 200

    def create_app(self):
        app = json.dumps({
            "name": self.app_name,
            "url": "https://www.example.com",
            "hook_attributes": {
                "url": "https://example.com/github/events",
            },
            "redirect_url": "https://example.com/callback",
            "public": False,
            "default_permissions": {
                "issues": "write",
                "checks": "write"
            },
            "default_events": [
                "issues",
                "issue_comment",
                "check_suite",
                "check_run"
            ]
        })
        r = self.post("settings/apps/new", data={'manifest': app})
        data = get_form_data(r.content, id='new_integration_manifest')
        r = self.post("settings/apps", data=data)
        soup = BeautifulSoup(r.content, 'html5lib')
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

    def install_app(self):
        r = self.get(f"apps/{self.app_id}/installations/new")
        data = get_form_data(r.content, **{'class': 'js-integrations-install-form'})
        data['install_target'] = 'all'
        r = self.post(f"apps/{self.app_id}/installations", data=data)
