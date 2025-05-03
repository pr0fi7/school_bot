import asyncio
from telethon import TelegramClient, functions, types
from telethon.tl.types import InputPeerChannel

api_id   = 23109567
api_hash = '3c490f463a93abf6b441d9e4dfdc9bae'

async def main(title, bot_username, teacher_username, language, phone_number=None):
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

if __name__ == '__main__':
    title = 'My channel – English'
    bot_username = '@uknow_uk_bot'
    teacher_username = '@pr0fi8'
    language = 'English'
    asyncio.run(main(title, bot_username, teacher_username, language))

# with TelegramClient('test', api_id, api_hash) as client:
#     result = client(functions.channels.CreateChannelRequest(
#         title='English Channel',
#         about='let\'s learn English together',
#         megagroup=True,
#         for_import=True,
#         forum=True,
#         geo_point=types.InputGeoPoint(
#             lat=50.84,
#             long=4.35,
#             accuracy_radius=42
#         ),
#         address='Brussels'
#                 ))
#     print(result.stringify())

# from telethon.tl.functions.channels import InviteToChannelRequest
# channel_id = 2549787605

# client = TelegramClient('test', api_id, api_hash)
# users_to_add = ["@pr0fi8"]  # Replace with the user ID you want to add
# async def main():
#     await client(InviteToChannelRequest(
#         channel_id,
#         users_to_add
#     ))

#update permissions
# async def main():
#     await client.edit_permissions(channel_id, user, timedelta(minutes=1),


# if __name__ == '__main__':
#     with client:
#         client.loop.run_until_complete(main())
# from telethon.sync import TelegramClient
# from telethon import functions, types
# from telethon.tl.types import PeerChannel

# api_id   = 23109567
# api_hash = '3c490f463a93abf6b441d9e4dfdc9bae'
# channel_id = 2549787605  # your supergroup’s numeric ID


# Adjust permissions for non-admins to prevent them from creating/editing forum topics
# with TelegramClient('session', api_id, api_hash) as client:
#     # 1) Tell Telethon: “this is a PeerChannel, not a PeerUser”
#     channel_peer = client.get_input_entity(PeerChannel(channel_id))

#     # 2) Build the default-banned-rights (disable forum-topic creation for non-admins)
#     banned = types.ChatBannedRights(
#         until_date=0,         # forever
#         manage_topics=True,    # forbid normal members from creating/editing topics
#         invite_users=True,      # forbid normal members from adding users
#     )

#     # 3) Push the new defaults
#     client(functions.messages.EditChatDefaultBannedRightsRequest(
#         peer=channel_peer,
#         banned_rights=banned
#     ))

#     print("✅ Non-admins can no longer create/edit forum topics.")

# from telethon.sync import TelegramClient
# from telethon import functions, types
# from telethon.tl.types import PeerChannel

# api_id   = 23109567
# api_hash = '3c490f463a93abf6b441d9e4dfdc9bae'
# channel_id = 2549787605  # your supergroup’s numeric ID

# # Close General topic (ID=1) to make it read-only for non-admins
# with TelegramClient('session', api_id, api_hash) as client:
#     # resolve the channel properly
#     channel_peer = client.get_input_entity(PeerChannel(channel_id))

#     # set closed=True to make it read-only for non-admins
#     result = client(functions.channels.EditForumTopicRequest(
#         channel   = channel_peer,
#         topic_id  = 1,
#         closed    = True      # only admins can post after this
#     ))
#     print("Closed 'General':", result)
