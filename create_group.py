import os

from dotenv import load_dotenv
from telethon import TelegramClient, functions, types
from telethon.tl.types import InputPeerChannel

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")


async def create_group(title, bot_username, teacher_username, language, phone_number=None):
    if phone_number:
        async with TelegramClient('session', api_id, api_hash) as client:
            await client.start(phone=phone_number)

    # 1) Start one async client session
    async with TelegramClient('session', api_id, api_hash) as client:
        # 2) Create the supergroup with forum enabled
        create_res = await client(functions.channels.CreateChannelRequest(
            title=title,
            about=f'Вивчаємо {language} разом',
            megagroup=True,
            forum=True
        ))
        new_chan = create_res.chats[0]
        channel_peer = InputPeerChannel(new_chan.id, new_chan.access_hash)

        # 3) Resolve your bot & teacher into InputPeerUser objects
        users = []
        for u in (bot_username, teacher_username):
            peer = await client.get_input_entity(u)
            users.append(peer)

        # 4) Invite them
        await client(functions.channels.InviteToChannelRequest(
            channel=channel_peer,
            users=users
        ))

        # 5) Disable topic‐creation for non-admins
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

        # 6) Close the “General” topic (ID=1)
        await client(functions.channels.EditForumTopicRequest(
            channel=channel_peer,
            topic_id=1,
            closed=True
        ))

        print("✅ Channel ready, users invited, forum creation disabled, General closed.")
