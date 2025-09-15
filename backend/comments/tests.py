import asyncio
import json
from websockets.asyncio.client import connect


async def main():

    async with connect(
            "ws://127.0.0.1:8000/ws/comments/",
            origin="http://localhost:5173"
    ) as ws:
        print("connected")
        await ws.send(json.dumps({"ping": "hello"}))
        while True:
            print("recv:", await ws.recv())

asyncio.run(main())
