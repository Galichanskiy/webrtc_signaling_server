#!/usr/bin/env python
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
        usr = msg['data']
        logger.info('Login action for user %s, saving its connection', usr)
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
    except Exception as e:
        logger.exception("Error while receiving messages")



start_server = websockets.serve(handler, '0.0.0.0', 5000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()