import os
import asyncio
import logging
from asyncio.subprocess import Process, PIPE

log = logging.getLogger('githubtest.localtunnel')


class Localtunnel:

    def __init__(self, process: Process, url: str):
        self.process = process
        self.url = url

    @classmethod
    async def start(cls, port='8080'):
        root = os.path.dirname(os.path.dirname(__file__))
        lt_js = os.path.join(root, 'node_modules/localtunnel/bin/lt.js')
        command = [lt_js, f'--port={port}']
        log.debug(' '.join(command))
        proc = await asyncio.create_subprocess_exec(*command, stdout=PIPE)
        data = await proc.stdout.readline()
        url = data.decode().strip()[len('your url is: '):]
        log.debug(url)
        return cls(proc, url)

    async def stop(self):
        self.process.terminate()
        await self.process.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(Localtunnel.start())
