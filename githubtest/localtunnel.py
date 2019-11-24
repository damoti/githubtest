import os
import asyncio
import logging
from typing import Optional
from asyncio import subprocess

log = logging.getLogger('githubtest.localtunnel')


class Localtunnel:

    def __init__(self, process: subprocess.Process, url: str):
        self.process = process
        self.url = url
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @classmethod
    async def start(cls, path: str, port: int):
        root = os.path.dirname(os.path.dirname(__file__))
        lt_js = os.path.join(root, path)
        command = [lt_js, f'--port={port}']
        log.debug(' '.join(command))
        proc = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE)
        data = await proc.stdout.readline()
        url = data.decode().strip()[len('your url is: '):]
        log.debug(url)
        return cls(proc, url)

    @classmethod
    def sync_start(cls, path: str, port: int):
        loop = asyncio.new_event_loop()
        localtunnel = loop.run_until_complete(cls.start(path, port))
        localtunnel._loop = loop
        return localtunnel

    async def stop(self):
        self.process.terminate()
        await self.process.wait()

    def sync_stop(self):
        self._loop.run_until_complete(self.stop())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(Localtunnel.start('node_modules/localtunnel/bin/lt.js', 8080))
