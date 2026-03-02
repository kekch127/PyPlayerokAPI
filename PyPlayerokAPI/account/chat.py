# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from typing import Optional

from .profile import ProfileMixin
from ..graphql import (
    build_query_payload,
    build_persisted_query_payload
)

from ..models.chat import ChatList, Chat, ChatMessageList, ChatMessage
from ..types.enums import ChatTypes, ChatStatuses
from ..types.exceptions import MissingAttributeError


class ChatMixin(ProfileMixin):
    """
    Миксин чатов
    """
    
    def get_chats(
        self,
        count: int = 24,
        type: Optional[ChatTypes] = None,
        status: Optional[ChatStatuses] = None,
        after_cursor: Optional[str] = None
    ) -> ChatList:
        """
        Получает все чаты аккаунта

        Args:
            count (int, optional): Кол-во чатов, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            type (Optional[ChatTypes], optional): Тип чатов, которые нужно получать (Все, если не указано). Defaults to None.
            status (Optional[ChatStatuses], optional): Статус чатов, которые нужно получать (Любые, если не указано). Defaults to None.
            after_cursor (Optional[str], optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            ChatList: Страница чатов
        """
        
        payload = build_persisted_query_payload(
            operation_name = "userChats",
            hash_key = "userChats",
            variables = {
                "pagination": {
                    "first": count,
                    "after": after_cursor
                },
                "filter": {
                    "userId": self.account_data.id,
                    "type": type.name if type else None,
                    "status": status.name if status else None
                },
                "hasSupportAccess": False
            }
        )
        
        response = self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("chats")
        
        return ChatList.model_validate(result)


    def get_chat(
        self,
        chat_id: str
    ) -> Chat:
        """
        Получить чат

        Args:
            chat_id (str): ID чата

        Returns:
            Chat: Модель чата
        """
        
        payload = build_persisted_query_payload(
            operation_name = "chat",
            hash_key = "chat",
            variables = {
                "id": chat_id,
                "hasSupportAccess": False
            }
        )

        response = self.transport.request(
            method = "get",
            payload = payload
        )

        result = response.json().get("data", {}).get("chat")

        return Chat.model_validate(result)
    
    
    def get_chat_by_username(
        self,
        username: str
    ) -> Optional[Chat]:
        """
        Получить чат по username собеседнка

        Args:
            username (str): username собеседнка

        Returns:
            Optional[Chat]: Модель чата
        """
        
        next_cursor = None
        while True:
            chats = self.get_chats(after_cursor = next_cursor)
            for chat in chats.chats:
                if any(user for user in chat.users if user.username.lower() == username.lower()): # type: ignore
                    return chat
                
            if not chats.page_info.has_next_page:
                break
            
            next_cursor = chats.page_info.end_cursor
    
    
    def get_chat_messages(
        self,
        chat_id: str,
        count: int = 24,
        after_cursor: Optional[str] = None
    ) -> ChatMessageList:
        """
        Получает сообщения чата

        Args:
            chat_id (str): ID чата
            count (int, optional): Кол-во сообщений, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            after_cursor (Optional[str], optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            ChatMessageList: Страница сообщений
        """
        
        payload = build_persisted_query_payload(
            operation_name = "chatMessages",
            hash_key = "chatMessages",
            variables = {
                "pagination": {
                    "first": count,
                    "after": after_cursor
                },
                "filter": {
                    "chatId": chat_id
                },
                "hasSupportAccess": False,
                "showForbiddenImage": True
            }
        )

        response = self.transport.request(
            method = "get",
            payload = payload
        )

        result = response.json().get("data", {}).get("chatMessages")

        return ChatMessageList.model_validate(result)
    
    
    def mark_chat_as_read(
        self,
        chat_id: str
    ) -> Chat:
        """
        Помечает чат как прочитанный (все сообщения)

        Args:
            chat_id (str): ID Чата

        Returns:
            Chat: Модель чата
        """
        
        payload = build_query_payload(
            operation_name = "markChatAsRead",
            query_key = "markChatAsRead",
            variables = {
                "input": {
                    "chatId": chat_id
                }
            }
        )
        
        response = self.transport.request(
            method = "post",
            payload = payload
        )

        result = response.json().get("data", {}).get("markChatAsRead")

        return Chat.model_validate(result)
    
    
    def send_message(
        self,
        chat_id: str,
        text: Optional[str] = None,
        photo_file_path: Optional[str] = None,
        mark_chat_as_read: bool = False
    ) -> ChatMessage:
        """
        Отправляет сообщение в чат.
        Можно отправить текстовое сообщение `text` или фотографию `photo_file_path`.

        Args:
            chat_id (str): ID чата
            text (Optional[str], optional): Текст сообщения. Defaults to None.
            photo_file_path (Optional[str], optional): Путь к файлу фотографии. Defaults to None.
            mark_chat_as_read (bool, optional): Пометить чат, как прочитанный перед отправкой. Defaults to False.

        Returns:
            ChatMessage: Модель отправленного сообщения
        """
        
        if not any([text, photo_file_path]):
            raise MissingAttributeError("Не был указан обязательный параметр: text/photo_file_path")
        
        if mark_chat_as_read:
            self.mark_chat_as_read(chat_id)
        
        pre_payload = build_query_payload(
            operation_name = "createChatMessage",
            query_key = "createChatMessage",
            variables = {
                "input": {
                    "chatId": chat_id
                }
            }
        )
        
        variables = pre_payload["variables"]
        
        if photo_file_path:
            variables["file"] = None # type: ignore
        
        if text:
            variables["input"]["text"] = text
        
        files = {"1": open(photo_file_path, "rb")} if photo_file_path else None
        map = {"1": ["variables.file"]} if photo_file_path else None
        
        payload = pre_payload if not files else {
            "operations": json.dumps(pre_payload), 
            "map": json.dumps(map)
        }
        
        response = self.transport.request(
            method = "post",
            payload = payload
        )

        result = response.json().get("data", {}).get("createChatMessage")

        return ChatMessage.model_validate(result)