import os
import sys
from datetime import datetime, timedelta
from typing import List

import telethon
import typer

from functools import wraps
from telethon import TelegramClient
from dotenv import load_dotenv
from telethon.tl import types

app = typer.Typer()
global client  # type: TelegramClient


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return client.loop.run_until_complete((f(*args, **kwargs)))
    return wrapper


def main():
    load_dotenv()
    global client
    if os.getenv('api_id') == "":
        print(".env not setup")
        sys.exit(0)
    client = TelegramClient('tg_cleanup', int(os.getenv('api_id')), os.getenv('api_hash'))
    client.start()


@app.command()
@coro
async def ls(user: bool = False):
    me = await client.get_me()
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if not user and dialog.is_user:
            continue
        msg = await client.get_messages(limit=0, entity=entity, from_user=me)
        if msg.total > 0:
            if dialog.is_group:
                print(entity.id, entity.title, ",", msg.total)
            if dialog.is_user:
                print(entity.id, entity.first_name, entity.last_name, ",", msg.total)
    await client.disconnect()
    pass


@app.command()
@coro
async def delete(entity_ids: List[int]):
    me = await client.get_me()
    yesterday = datetime.now() - timedelta(hours = 1)
    for entity_id in entity_ids:
        try:
            entity = await client.get_entity(entity_id)
            msgs = await client.get_messages(limit=None, entity=entity, from_user=me, offset_date=yesterday)
            await client.delete_messages(entity=entity, message_ids=msgs)
            if (isinstance(entity, (types.Chat, types.ChatForbidden)) or
                    (isinstance(entity, types.Channel) and entity.megagroup)):
                print("deleted", entity.id, entity.title, ",", msgs.total)
            if isinstance(entity, types.User):
                print("deleted", entity.id, entity.first_name, entity.last_name, ",", msgs.total)
        except telethon.errors.rpcerrorlist.ChannelPrivateError:
            print(f'{entity_id} has leaved or kicked',)
            continue
        except ValueError:
            print('Error as expected')
            continue
    await client.disconnect()
    pass


if __name__ == '__main__':
    main()
    app()
