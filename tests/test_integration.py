import os
from unittest import TestCase
from githubtest import GitHubTestUser


class TestGitHubUser(TestCase):

    @classmethod
    def setUpClass(cls):
        otp_secret = os.environ['TEST_OTP']
        username = os.environ['TEST_USERNAME']
        password = os.environ['TEST_PASSWORD']
        cls.ghu = GitHubTestUser.connect('python githubtest', otp_secret, username, password)

    def test(self):
        ghu = self.ghu
        print('login successful')
        if not ghu.app_exists():
            print('creating')
            ghu.create_app()
            print('app created')
        else:
            print('already exists')
        #gha.install_app()
        #print('app installed')
        #installs = ghu.api.app_installations()
        #a = 3
