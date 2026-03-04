import pytest
from PyPlayerokAPI.stream.listener.chat_storage import ChatStorage
from PyPlayerokAPI.models.chat import Chat

@pytest.mark.asyncio
async def test_chat_storage():

    storage = ChatStorage()

    chat = Chat(id="chat1")

    await storage.upsert(chat)

    result = await storage.get("chat1")

    assert result == chat