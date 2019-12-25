import os
import asyncio
from urllib.parse import urlparse
from unittest import IsolatedAsyncioTestCase

from githubtest.ngrok import Ngrok
from githubtest.user import GitHubTestUser
from githubtest.utils import get_external_ip


class GitHubTestCase(IsolatedAsyncioTestCase):

    api: GitHubTestUser

    APP_PORT = 8080
    APP_MANIFEST = {}

    @classmethod
    def setUpClass(cls):
        if 'NGROK_TOKEN' in os.environ:
            loop = asyncio.get_event_loop()
            ngrok = Ngrok()
            loop.run_until_complete(ngrok.ensure())
            loop.run_until_complete(ngrok.authenticate(os.environ['NGROK_TOKEN']))
            loop.run_until_complete(ngrok.start())
            cls.addClassCleanup(ngrok.stop)
            tunnel = loop.run_until_complete(ngrok.create_tunnel(addr=str(cls.APP_PORT)))
            webhook = tunnel['public_url']
        else:
            webhook = f"http://{get_external_ip()}:{cls.APP_PORT}"

        cls.APP_MANIFEST["name"] += f" {urlparse(webhook).netloc}"
        if len(cls.APP_MANIFEST["name"]) > 34:  # GitHub does not allow names longer than 34.
            cls.APP_MANIFEST["name"] = cls.APP_MANIFEST["name"][:34]
        cls.APP_MANIFEST["hook_attributes"]["url"] = webhook

        api = GitHubTestUser.connect(
            cls.APP_MANIFEST,
            os.environ['TEST_OTP'],
            os.environ['TEST_OAUTH'],
            os.environ['TEST_USERNAME'],
            os.environ['TEST_PASSWORD']
        )
        api.ensure_app()
        api.ensure_install()
        cls.addClassCleanup(api.disconnect)

        cls.api = api

    @classmethod
    def tearDownClass(cls):
        cls.api.delete_app()
