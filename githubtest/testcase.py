import os
from urllib.parse import urlparse
from unittest import IsolatedAsyncioTestCase

from githubtest.localtunnel import Localtunnel
from githubtest.user import GitHubTestUser
from githubtest.utils import get_external_ip


class GitHubTestCase(IsolatedAsyncioTestCase):

    APP_PORT = 8080
    APP_MANIFEST = {}

    @classmethod
    def setUpClass(cls):
        if 'TEST_USE_LOCALTUNNEL' in os.environ:
            tunnel = Localtunnel.sync_start(os.environ['TEST_USE_LOCALTUNNEL'], cls.APP_PORT)
            cls.addClassCleanup(tunnel.sync_stop)
            webhook = tunnel.url
        else:
            webhook = f"http://{get_external_ip()}:{cls.APP_PORT}"

        cls.APP_MANIFEST["name"] += f" {urlparse(webhook).netloc}"
        cls.APP_MANIFEST["hook_attributes"]["url"] = webhook

        api = GitHubTestUser.connect(
            cls.APP_MANIFEST,
            os.environ['TEST_OTP'],
            os.environ['TEST_USERNAME'],
            os.environ['TEST_PASSWORD']
        )
        api.ensure_app()
        api.ensure_install()

        cls.api = api
