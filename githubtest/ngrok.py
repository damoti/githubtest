import os
import json
import zipfile
import asyncio
import logging
import aiohttp
from typing import Optional, Tuple


DOWNLOAD_URL = "https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip"


log = logging.getLogger('githubtest.ngrok')


class NgrokProcessProtocol(asyncio.SubprocessProtocol):

    def __init__(self):
        self.ready = asyncio.Event()
        self.api = None

    def pipe_data_received(self, fd, data):
        for line in data.decode().splitlines():
            try:
                msg = json.loads(line)
            except:
                log.warning(line)
                continue
            lvl = msg.get('lvl', 'info')
            if lvl == 'info':
                log.info(msg['msg'])
                if msg['msg'] == 'starting web service':
                    self.api = msg['addr']
                if msg['msg'] == 'client session established':
                    self.ready.set()
            elif lvl == 'warn':
                log.warning(msg['msg'])
            elif lvl in ('eror', 'crit'):
                log.error(msg['msg'])
                log.error(msg['err'])


class Ngrok:

    def __init__(self):
        self.directory = os.path.join(
            os.path.dirname(__file__), 'bin'
        )
        self.bin = os.path.join(self.directory, 'ngrok')
        self.protocol: Optional[NgrokProcessProtocol] = None
        self.transport: Optional[asyncio.SubprocessTransport] = None

    async def authenticate(self, token):
        command = self.bin, 'authtoken', token
        proc = await asyncio.create_subprocess_exec(*command)
        await proc.wait()

    @staticmethod
    async def execute(command) -> Tuple[asyncio.SubprocessTransport, NgrokProcessProtocol]:
        loop = asyncio.get_event_loop()
        return await loop.subprocess_exec(
            NgrokProcessProtocol, *command
        )

    async def start(self):
        command = self.bin, 'start', '--none', '--log=stdout', '--log-format=json'
        log.debug(' '.join(command))
        self.transport, self.protocol = await self.execute(command)
        await asyncio.wait_for(self.protocol.ready.wait(), 15.0)

    def stop(self):
        self.transport.terminate()
        self.transport.close()

    async def create_tunnel(self, name="untitled", proto="http", addr="8080"):
        data = {'name': name, 'proto': proto, 'addr': addr}
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{self.protocol.api}/api/tunnels', json=data) as resp:
                return await resp.json()

    async def list_tunnels(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{self.protocol.api}/api/tunnels') as resp:
                return await resp.json()

    @property
    def exists(self):
        return os.path.exists(self.bin)

    async def download(self):
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        downloaded_file = os.path.join(
            self.directory, DOWNLOAD_URL[DOWNLOAD_URL.rfind('/')+1:]
        )

        if not os.path.exists(downloaded_file):
            log.info('Downloading: %s', DOWNLOAD_URL)
            async with aiohttp.ClientSession() as session:
                async with session.get(DOWNLOAD_URL) as resp:
                    with open(downloaded_file, 'wb') as fd:
                        while True:
                            chunk = await resp.content.read(65536)
                            if not chunk:
                                break
                            fd.write(chunk)

        log.info('Extracting: %s', downloaded_file)
        with zipfile.ZipFile(downloaded_file) as dotzip:
            dotzip.extractall(self.directory)
            os.chmod(self.bin, 0o755)

        return self.exists

    async def ensure(self):
        return self.exists or await self.download()


async def test():
    ngrok = Ngrok()
    await ngrok.ensure()
    await ngrok.start()
    log.info(ngrok.protocol.api)
    tunnel = await ngrok.create_tunnel()
    log.info(tunnel['public_url'])
    tunnels = await ngrok.list_tunnels()
    log.info(json.dumps(tunnels, indent=4))
    await ngrok.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test())
