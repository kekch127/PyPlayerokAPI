# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import os
import tempfile
import shutil
import mimetypes
from typing import Literal, Optional, Dict
from logging import getLogger

import curl_cffi

from .types.exceptions import (
    CloudflareDetected,
    RequestError,
    RequestFailedError,
)


class Transport:
    base_url: str = "https://playerok.com"
    
    def __init__(
        self,
        token: str,
        user_agent: str,
        proxy: Optional[str] = None,
        requests_timeout: int = 15,
        request_max_retries: int = 5,
    ):
        self.token = token
        self.user_agent = user_agent
        self.proxy = proxy
        self.requests_timeout = requests_timeout
        self.request_max_retries = request_max_retries
        self._proxy_string = (
            f"http://{self.proxy.replace('https://', '').replace('http://', '')}"
            if self.proxy
            else None
        )
        
        self.__curl_session: curl_cffi.AsyncSession = None # type: ignore

        self.logger = getLogger("playerokapi")

        self._cert_path = os.path.join(os.path.dirname(__file__), "cacert.pem")
        self._tmp_cert_path = os.path.join(tempfile.gettempdir(), "cacert.pem")
        shutil.copyfile(self._cert_path, self._tmp_cert_path)

        self._refresh_clients()

    def _refresh_clients(self):
        self.__curl_session = curl_cffi.AsyncSession(
            impersonate = "chrome",
            timeout = 10,
            proxy = self._proxy_string,
            verify = self._tmp_cert_path # type: ignore
        )

    async def request(
        self,
        method: Literal["get", "post"],
        url: str = "https://playerok.com/graphql",
        headers: Dict[str, str] = {"accept": "*/*"},
        payload: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ):

        x_gql_op = (
            payload.get("operationName", "viewer")
            if isinstance(payload, dict)
            else "viewer"
        )

        default_headers = {
            "accept": "*/*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "access-control-allow-headers": "sentry-trace, baggage",
            "apollo-require-preflight": "true",
            "apollographql-client-name": "web",
            "content-type": "application/json",
            "cookie": f"token={self.token}",
            "origin": "https://playerok.com",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\", \"Not_A Brand\";v=\"99\"",
            "sec-ch-ua-arch": "\"x86\"",
            "sec-ch-ua-bitness": "\"64\"",
            "sec-ch-ua-full-version": "\"144.0.7559.110\"",
            "sec-ch-ua-full-version-list": "Not(A:Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"144.0.7559.110\", \"Google Chrome\";v=\"144.0.7559.110\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": "\"\"",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"19.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.user_agent,
            "x-gql-op": x_gql_op,
            "x-gql-path": "/",
            "x-timezone-offset": "-240"
        }

        headers = {**default_headers, **headers}

        async def make_request():
            for _ in range(3):
                try:
                    if method == "get":
                        return await self.__curl_session.get(
                            url = url,
                            params = payload,
                            headers = headers,
                            timeout = self.requests_timeout,
                        )

                    if files:
                        # Автор: ChatGPT.
                        # Для отправки файлов (я честно до сих пор особо не понимаю, как это дерьмо работает) 
                        
                        # Запрос выглядит примерно так
                        # =================================================================
                        # POST /graphql
                        # Content-Type: multipart/form-data; boundary=----...

                        # ------boundary
                        # Content-Disposition: form-data; name="operations"

                        # {...json...}

                        # ------boundary
                        # Content-Disposition: form-data; name="map"

                        # {"1":["variables.attachments.0"]}

                        # ------boundary
                        # Content-Disposition: form-data; name="1"; filename="banner.jpg"
                        # Content-Type: image/jpeg

                        # <binary image data>

                        # ------boundary--
                        # =================================================================
                        # По сути нужно передать в multipart 3 части:
                        # 1. operaions - JSON GraphQL запроса
                        # 2. map - куда отправлять дайлы
                        # 3. сами файлы
                        
                        # Удаляем header потому что multipart заголовок выглядит так: Content-Type: multipart/form-data; boundary=----abc123
                        # boundary генерируется автоматически libcurl, если оставить application/json - сервер не поймет запрос
                        headers.pop("content-type", None)
                        
                        # Обертка над libcurl mime API (по сути билдер multipart запроса)
                        mime = curl_cffi.CurlMime()

                        if payload:
                            # Создает multipart часть
                            # =================================================================
                            # Content-Disposition: form-data; name="operations"
                            #
                            # {json}
                            # =================================================================
                            # или
                            # =================================================================
                            # Content-Disposition: form-data; name="map"
                            #
                            # {json}
                            # =================================================================
                            # data= означает строка или bytes
                            for k, v in payload.items():
                                mime.addpart(name = k, data = v)

                        # Обертка над файлами. Файлы приходят в формате
                        # {"1": open("banner.jpg","rb")} или {"1": ("banner.jpg", file)}
                        for name, file_tuple in files.items():
                            # определяем имя файла (filename) для header: Content-Disposition: form-data; name="1"; filename="banner.jpg"
                            # а объект (fileobj) определяем для стриминга в HTTP запрос (по сути говорим libcurl - открой файл и стримь в HTTP запрос)
                            if isinstance(file_tuple, tuple):
                                filename = file_tuple[0]
                                fileobj = file_tuple[1]
                            else:
                                fileobj = file_tuple
                                filename = getattr(fileobj, "name", "file")

                            # определяем MIME (Это добавляет header: Content-Type: image/jpeg)
                            # Пример:
                            # banner.jpg → image/jpeg
                            # banner.png → image/png
                            mime_type, _ = mimetypes.guess_type(filename)
                            if mime_type is None:
                                mime_type = "application/octet-stream"

                            # Генерим сами мультипары
                            #
                            # ------boundary
                            # Content-Disposition: form-data; name="1"; filename="banner.jpg"
                            # Content-Type: image/jpeg
                            #
                            # <binary data>
                            mime.addpart(
                                name = name,
                                filename = filename,
                                local_path = fileobj.name, 
                                content_type = mime_type
                            )

                        return await self.__curl_session.post(
                            url = url,
                            headers = headers,
                            multipart = mime,
                            timeout = self.requests_timeout,
                        )

                    return await self.__curl_session.post(
                        url = url,
                        json = payload,
                        headers = headers,
                        timeout = self.requests_timeout,
                    )

                except Exception as e:
                    self.logger.debug(f"Ошибка запроса: {e}")
            
            raise Exception("Не удалось выполнить запрос")


        cloudflare_signatures = [
            "<title>Just a moment...</title>",
            "window._cf_chl_opt",
            "Enable JavaScript and cookies to continue",
            "Checking your browser before accessing",
            "cf-browser-verification",
            "Cloudflare Ray ID"
        ]

        for attempt in range(self.request_max_retries):
            response = await make_request()
            
            if response is None:
                continue

            if not any(sig in response.text for sig in cloudflare_signatures):
                break

            # закрываем текущую сессию и создаем новую
            await self.close()
            self._refresh_clients()
            
            delay = min(120.0, 5.0 * (2 ** attempt))
            
            self.logger.warning(f"Обнаружен Cloudflare, повтор через {delay} секунд")
            await asyncio.sleep(delay)

        else:
            raise CloudflareDetected(response) # type: ignore

        if response.status_code != 200:
            raise RequestFailedError(response) # type: ignore
        
        if "application/json" in response.headers.get("content-type", ""): # <-- Проверяем header чтобы не глотнуть HTML от Cloudflare => не получить Exception от JSONDecodeError
            json_data = response.json()
            if "errors" in json_data:
                raise RequestError(response) # type: ignore

        return response

    async def close(self):
        await self.__curl_session.close()