import asyncio
import aiohttp
import json
import websockets
import random
import string
import requests
import time
LINK = 'http://control/api/v1/free'

async def hello():
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(LINK) as resp:
                data = await resp.json()
            if type(data['free']) != str:
                async with websockets.connect('ws://%s:%s' % (data['free']['ip'], data['free']['port'])) as websocket:
                        message = ''.join([random.choice(string.ascii_letters) for n in range(32)])
                        await websocket.send(message)
                        print("> {}".format(message))

                        greeting = await websocket.recv()
                        print("< {}".format(greeting))
                        await asyncio.sleep(random.randint(15,45))
            else:
                print('Server says there is no avaliable user slots.')
                await asyncio.sleep(random.randint(5,15))


async def main():
    await asyncio.gather(
        hello(),
        hello(),
        hello(),
        hello(),
        hello(),
        hello(),
        hello(),
        hello(),
    )

asyncio.get_event_loop().run_until_complete(main())