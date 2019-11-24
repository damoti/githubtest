from githubtest.testcase import GitHubTestCase
from githubtest.server import GitHubAppServer


class TestGitHubUser(GitHubTestCase):

    APP_MANIFEST = {
        "name": "PyGitHubTest",
        "url": "https://www.example.com",
        "hook_attributes": {
            "url": None,
        },
        "redirect_url": "https://example.com/callback",
        "public": False,
        "default_events": [
            "push",
        ],
        "default_permissions": {
            "contents": "write",
        },
    }

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.server = GitHubAppServer(self.APP_PORT)
        await self.server.start()
        self.addAsyncCleanup(self.server.stop)

    async def test(self):
        user = self.api.get_user_api()
        repo = next(user.repositories(), None)
        if not repo:
            repo = user.create_repository('test-repo', auto_init=True)
        readme = repo.file_contents('README.md')
        readme.update('changed the readme', b'new readme content')
        push = await self.server.events.where(lambda e: e.event == 'push')
        self.assertEqual(push.payload['head_commit']['message'], 'changed the readme')
