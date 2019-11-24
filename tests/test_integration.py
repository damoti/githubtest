import os
import json
import asyncio
from unittest import IsolatedAsyncioTestCase
from githubtest import GitHubTestUser
from aiohttp import web


class TestGitHubUser(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        otp_secret = os.environ['TEST_OTP']
        username = os.environ['TEST_USERNAME']
        password = os.environ['TEST_PASSWORD']
        cls.ghu = GitHubTestUser.connect('python githubtest', otp_secret, username, password)

    async def test(self):
        ghu = self.ghu
        print('login successful')
        if not ghu.app_exists():
            print('creating')
            ghu.create_app()
            print('app created')
        else:
            print('app already exists')

        api = ghu.get_app_api()

        if not next(api.app_installations(), None):
            ghu.install_app()
            print('app installed')
        else:
            print('app already installed')

        gh = ghu.user_api

        if not next(gh.repositories(), None):
            gh.create_repository('test-repo', auto_init=True)

        app = web.Application()
        runner = web.AppRunner(app)

        async def hello(request):
            d = await request.json()
            print(json.dumps(d, indent=4))
            return web.Response(text="{'status': 'received'}")
        app.add_routes([web.post('/', hello)])

        await runner.setup()
        site = web.TCPSite(runner)
        await site.start()

        repo = gh.repository(os.environ['TEST_USERNAME'], 'test-repo')
        readme = repo.file_contents('README.md')
        readme.update('changed', b'new readme content')

        await asyncio.sleep(10)
