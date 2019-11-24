from aiohttp import web
from streamcontroller import StreamController


class GitHubEvent:
    def __init__(self, event, payload):
        self.event = event
        self.payload = payload


class GitHubAppServer:

    def __init__(self, port: int):
        self.port = port
        app = web.Application()
        app.add_routes([web.post('/', self.handle_request)])
        self.runner = web.AppRunner(app)
        self._event_controller = StreamController()
        self.events = self._event_controller.stream

    async def start(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, port=self.port)
        await site.start()

    async def stop(self):
        await self.runner.cleanup()

    async def handle_request(self, request):
        d = await request.json()
        event = GitHubEvent(request.headers['X-GitHub-Event'], d)
        self._event_controller.add(event)
        return web.Response(text="{'status': 'received'}")
