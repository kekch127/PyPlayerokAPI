# -*- coding=utf-8 -*-

import requests


class CloudflareDetected(Exception):
    # Обнаружение Cloudflare защиты при отправке запроса
    
    def __init__(
        self,
        response: requests.Response
    ):
        self.response = response
        self.status_code = self.response.status_code
        self.html_text = self.response.text
    
    def __str__(self):
        msg = (
            "Cloudflare заметил подозрительную активность при отправке запроса на Playerok."
            f"\nКод ошибки: {self.status_code}"
            f"\nОтвет: {self.html_text}"
        )
        
        return msg


class RequestFailedError(Exception):
    # Ошибка, когда код ответа не 200
    
    def __init__(
        self,
        response: requests.Response
    ):
        self.response = response
        self.status_code = self.response.status_code
        self.html_text = self.response.text

    def __str__(self):
        msg = (
            f"Ошибка запроса к {self.response.url}"
            f"\nКод ошибки: {self.status_code}"
            f"\nОтвет: {self.html_text}"
        )
        
        return msg


class RequestError(Exception):
    # Ошибка при отправке запроса
    
    def __init__(
        self,
        response: requests.Response
    ):
        self.response = response
        self.json = response.json()
        self.error_code = self.json["errors"][0]["extensions"]["code"]
        self.error_message = self.json["errors"][0]["message"]

    def __str__(self):
        msg = (
            f"Ошибка запроса к {self.response.url}"
            f"\nКод ошибки: {self.error_code}"
            f"\nСообщение: {self.error_message}"
        )
        
        return self.error_message or msg


class UnauthorizedError(Exception):
    # Ошибка авторизации аккаунта
    
    def __str__(self):
        return "Не удалось авторизоваться на Playerok. Проверьте указанный token"


class MissingAttributeError(Exception):
    pass