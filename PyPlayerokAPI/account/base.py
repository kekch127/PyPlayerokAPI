# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from ..transport import Transport


class AccountBase:
    """
    Базовый класс аккаунта.

    Отвечает только за:
    - хранение токена
    - инициализацию transport
    - базовые настройки клиента

    Не является Singleton.
    """

    def __init__(
        self,
        token: str,
        user_agent: str = "",
        proxy: Optional[str] = None,
        requests_timeout: int = 15,
        request_max_retries: int = 5,
    ) -> None:

        if not token:
            raise ValueError("Token не может быть пустым")

        self.token = token
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/144.0.0.0 Safari/537.36"
        )

        self.transport = Transport(
            token = self.token,
            user_agent = self.user_agent,
            proxy = proxy,
            requests_timeout = requests_timeout,
            request_max_retries = request_max_retries,
        )