#!/usr/bin/env python3.5

import asyncio
import websockets
import json
import signal
import uuid 

USERNB = 100

usr = {}

async def connect_and_login():
    user_id = uuid.uuid1()
    try:
        async with websockets.client.connect('ws://0.0.0.0:5000') as websocket:
            usr[user_id] = True
            while True:
                login_action = {"action":"login","data":str(user_id)}
                await websocket.send(json.dumps(login_action))
                await asyncio.sleep(10)
    except:
        pass

async def print_client_nb():
    while True:
        print("NB connected users: %s" % len(usr))
        await asyncio.sleep(2)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(print_client_nb())
    
    for i in range(USERNB):
        loop.create_task(connect_and_login())

    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        print("Attempting graceful shutdown", flush=True)
        def shutdown_exception_handler(loop, context):
            if "exception" not in context \
            or not isinstance(context["exception"], asyncio.CancelledError):
                loop.default_exception_handler(context)
        loop.set_exception_handler(shutdown_exception_handler)

        tasks = asyncio.gather(*asyncio.Task.all_tasks(loop=loop), loop=loop, return_exceptions=True)
        tasks.add_done_callback(lambda t: loop.stop())
        tasks.cancel()

        while not tasks.done() and not loop.is_closed():
            loop.run_forever()
    finally:
        loop.close()