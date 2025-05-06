import os
import requests

from dotenv import load_dotenv

from telethon import TelegramClient, functions, types
from telethon.tl.types import InputPeerChannel

from database.models import school_db

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
phone_number = os.getenv("PHONE_NUMBER")


async def create_group(title, bot_username, teacher_id, language):
    # 1) Create the client and start it (login + save session)
    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone_number)

    # 2) Create the channel
    create_res = await client(functions.channels.CreateChannelRequest(
        title=title,
        about=f'Вивчаємо {language} разом',
        megagroup=True,
        forum=True
    ))
    new_chan = create_res.chats[0]
    channel_peer = InputPeerChannel(new_chan.id, new_chan.access_hash)

    # 3) Invite bot & teacher
    bot_entity = await client.get_input_entity(bot_username)
    await client(functions.channels.InviteToChannelRequest(
        channel=channel_peer,
        users=[bot_entity]
    ))

    invite = await client(functions.messages.ExportChatInviteRequest(
        peer=channel_peer
    ))

    # 4) Disable topic creation for non-admins
    banned = types.ChatBannedRights(
        until_date=0,
        manage_topics=True,
        invite_users=True,
        pin_messages=True,
        change_info=True,
    )
    await client(functions.messages.EditChatDefaultBannedRightsRequest(
        peer=channel_peer,
        banned_rights=banned
    ))

    raw_id = new_chan.id
    new_group_id = int(f"-100{raw_id}")
    school_db.update_teacher_group(teacher_id, new_group_id, invite.link)
    text = (
        f"Вітаю! Ваш запит було схвалено.\n"
        f"Група для комунікації зі студентами створена.\n"
        f"Приєднуйтесь за посиланням:\n"
        f"{invite.link}"
    )

    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": teacher_id, "text": text}
    )
    response.raise_for_status()

    # 5) Close “General” topic
    await client(functions.channels.EditForumTopicRequest(
        channel=channel_peer,
        topic_id=1,
        closed=True
    ))

    # 6) Promote bot to full admin
    admin_rights = types.ChatAdminRights(
        change_info=True,
        post_messages=True,
        edit_messages=True,
        delete_messages=True,
        ban_users=True,
        invite_users=True,
        pin_messages=True,
        add_admins=True,
        anonymous=False,
        manage_call=True,
        other=True,
        manage_topics=True,
    )
    bot_peer = await client.get_input_entity(bot_username)
    await client(functions.channels.EditAdminRequest(
        channel=channel_peer,
        user_id=bot_peer,
        admin_rights=admin_rights,
        rank='Administrator'
    ))

    print("Channel ready: reverted to forum channel, users invited, general topic closed, bot got admin rights. ✅")

import asyncio
from telethon import TelegramClient, functions, types
from telethon.tl.types import InputPeerChannel
import os 
import dotenv
dotenv.load_dotenv()

# Load environment variables from .env file
api_id   = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')


async def main(phone, title, bot_username, teacher_username, language):
    # 1) Create the client and start it (login + save session)
    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)     # prompts only once for code if needed

    # 2) Create the channel
    create_res = await client(functions.channels.CreateChannelRequest(
        title=title,
        about=f'Вивчаємо {language} разом',
        megagroup=True,
        forum=True
    ))
    new_chan     = create_res.chats[0]
    channel_peer = InputPeerChannel(new_chan.id, new_chan.access_hash)

    # 3) Invite bot & teacher
    users = [await client.get_input_entity(u) for u in (bot_username, teacher_username)]
    await client(functions.channels.InviteToChannelRequest(
        channel=channel_peer,
        users=users
    ))

    # 4) Disable topic creation for non-admins
    banned = types.ChatBannedRights(
        until_date=0,
        manage_topics=True,
        invite_users=True,
        pin_messages=True,
        change_info=True,
    )
    await client(functions.messages.EditChatDefaultBannedRightsRequest(
        peer=channel_peer,
        banned_rights=banned
    ))

    # 5) Close “General” topic
    await client(functions.channels.EditForumTopicRequest(
        channel=channel_peer,
        topic_id=1,
        closed=True
    ))

    # 6) Promote bot to full admin
    admin_rights = types.ChatAdminRights(
        change_info   = True,
        post_messages = True,
        edit_messages = True,
        delete_messages=True,
        ban_users     = True,
        invite_users  = True,
        pin_messages  = True,
        add_admins    = True,
        anonymous     = False,
        manage_call   = True,
        other         = True,
        manage_topics = True,
    )
    bot_peer = await client.get_input_entity(bot_username)
    await client(functions.channels.EditAdminRequest(
        channel      = channel_peer,
        user_id      = bot_peer,
        admin_rights = admin_rights,
        rank         = 'Administrator'
    ))

    print("✅ All done.")
    await client.disconnect()  # clean up

if __name__ == '__main__':
    phone   = '+32471069627'
    title   = 'My channel – English'
    bot     = '@uknow_uk_bot'
    teacher = '@pr0fi8'
    lang    = 'English'
    asyncio.run(main(phone, title, bot, teacher, lang))
