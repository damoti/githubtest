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
    async def start(cls, localtunnel_path: str, port: int):
        command = [localtunnel_path, f'--port={port}']
        log.debug(' '.join(command))
        print('tunnel sub process starting')
        proc = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE)
        print('tunnel readline')
        data = await proc.stdout.readline()
        print(f'read: {data}')
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
    root = os.path.dirname(os.path.dirname(__file__))
    lt_js = os.path.join(root, 'node_modules/localtunnel/bin/lt.js')
    asyncio.run(Localtunnel.start(lt_js, 8080))
