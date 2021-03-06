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
        repo = await user.async_first_repositories()
        if not repo:
            repo = await user.async_create_repository('test-repo', auto_init=True)
            await self.server.events.where(lambda e: e.event == 'push')
        readme = await repo.async_file_contents('README.md')
        await readme.async_update('changed the readme', b'new readme content')
        push = await self.server.events.where(lambda e: e.event == 'push')
        self.assertEqual(push.payload['head_commit']['message'], 'changed the readme')
