#!/usr/bin/env python3.5
"""Websocket server programm

The purpose of this code is to assume the role of a signaling server 
in the process of a webrtc connection establishement
"""

import asyncio
import websockets
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cons = dict()


async def handler(websocket, path):
    """Method that launch tasks to handle websocket connection
    """
    try:
        ws_task = asyncio.ensure_future(ws_con_handler(websocket))
        done, pending = await asyncio.wait(
            [ws_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except Exception as e:
        logger.exception("Error while launching websocket handler task")

async def send_to(con, message):
    """Method that send the message to the connection arg
    """
    try:
        await con.send(json.dumps(message))
    except Exception as e:
        logger.exception("Error while sending message to 'peer'")


def login_action(con, msg):
    """Method that is fired on the login action
    It stores the websocket connection to a dict for the futur actions
    """
    if 'data' in msg:
        if msg['data'] not in cons:
            usr = msg['data']
            logger.debug('Login action for user %s, saving its connection', usr)
            cons[usr] = con
    else:
        raise Exception("Can't find 'data' key on received message")

async def send_message_to(msg, to):
    """Utiliy method that 'stringify' the message
    and get the connection, thanks to the 'to' arg, from the dict
    """
    msg_str = json.dumps(msg)
    logger.info('Sending message %s to %s', msg_str, to)
    await send_to(cons[msg['to']], msg)

async def ws_con_handler(ws):
    """Method that wait for websocket message
    and handle them in function of their actions
    """
    try:
        while True:
            msg = json.loads(await ws.recv())
            if 'action' in msg:
                if msg['action'] == 'login':
                    login_action(ws, msg)
                else:
                    if 'to' in msg:
                        logger.info('Send message to %s',msg['to'])
                        await send_to(cons[msg['to']], msg)
                    else:
                        raise Exception('No \'to\' key on received message')
            else:
                raise Exception('No \'action\' key on received message')
    except websockets.exceptions.ConnectionClosed as e:
        logger.info("Connection closed")
    except Exception as e:
        logger.exception("Error while receiving messages")




if __name__ == '__main__':
    start_server = websockets.serve(handler, '0.0.0.0', 5000)
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(start_server)
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