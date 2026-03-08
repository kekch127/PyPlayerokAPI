# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from typing import Optional, List, Optional

from .profile import ProfileMixin
from ..graphql import (
    build_query_payload,
    build_persisted_query_payload,
)
from ..models.transaction import (
    Transaction,
    TransactionList,
    TransactionProvider,
    TransactionOperations
)
from ..types.enums import (
    TransactionProviderIds,
    TransactionPaymentMethodIds,
    TransactionStatuses,
    TransactionProviderDirections
)


class TransactionsMixin(ProfileMixin):
    """
    Миксин для работы с транзакциями.
    """
    
    async def get_transactions(
        self,
        count: int = 24,
        operation: Optional[TransactionOperations] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        provider_id: Optional[TransactionProviderIds] = None,
        status: Optional[TransactionStatuses] = None,
        after_cursor: Optional[str] = None
    ) -> TransactionList:
        """
        Возвращает список всех транзакций аккаунта.

        Args:
            count (int, optional): Кол-во операций, которое необходимо получить (не более 24 за один запрос). Defaults to 24.
            operation (Optional[TransactionOperations], optional): Операция транзакции. Defaults to None.
            min_value (Optional[int], optional): Минимальная сумма транзакции. Defaults to None.
            max_value (Optional[int], optional): Максимальная сумма транзакции. Defaults to None.
            provider_id (Optional[TransactionProviderIds], optional): ID провайдера транзакции. Defaults to None.
            status (Optional[TransactionStatuses], optional): Статус транзакции. Defaults to None.
            after_cursor (Optional[str], optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            TransactionList: Лист(страница) транзакицй
        """
        
        variables = {
            "pagination": {
                "first": count,
                "after": after_cursor
            },
            "filter": {
                "userId": await self.get_account_property("id") # self.account_data.id,
            },
            "hasSupportAccess": False
        }
        
        filter_section = variables["filter"]
        
        # фильтр по операции
        if operation:
            filter_section["operation"] = [operation.name]
        
        # фильтр по сумме
        if min_value is not None or max_value is not None:
            value_filter = {}
            
            if min_value is not None:
                value_filter["min"] = str(min_value)
            if max_value is not None:
                value_filter["max"] = str(max_value)
            
            filter_section["value"] = value_filter
        
        #фильтр по провайдеру
        if provider_id:
            filter_section["providerId"] = [provider_id.name]
        
        # фильтр по статусу
        if status:
            filter_section["status"] = [status.name]
        
        payload = build_persisted_query_payload(
            operation_name = "transactions",
            hash_key = "transactions",
            variables = variables
        )

        # GraphQL требует строки
        payload["variables"] = json.dumps(payload["variables"])
        payload["extensions"] = json.dumps(payload["extensions"])
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        data = response.json().get("data", {}).get("transactions")
        
        return TransactionList.model_validate(data)


    async def get_transaction_providers(
        self,
        direction: TransactionProviderDirections = TransactionProviderDirections.IN
    ) -> List[TransactionProvider]:
        """
        Возвращает список всех провайдеров транзакций.

        Args:
            direction (TransactionProviderDirections, optional): Напарвление транзакций (пополнение/вывод). Defaults to TransactionProviderDirections.IN.

        Returns:
            List[TransactionProvider]: Список провайдеров транзакций
        """
        payload = build_persisted_query_payload(
            operation_name = "transactionProviders",
            hash_key = "transactionProviders",
            variables = {
                "filter": {
                    "direction": direction.name 
                }
            }
        )
        
        # GraphQL требует дампа
        payload["variables"] = json.dumps(payload["variables"])
        payload["extensions"] = json.dumps(payload["extensions"])
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        providers = response.json().get("data", {}).get("transactionProviders")
        
        return [TransactionProvider.model_validate(p) for p in providers]


    async def remove_transaction(
        self,
        transaction_id: str
    ) -> Transaction:
        """
        Удаляют транзакцию (например: можно отменить вывод)

        Args:
            transaction_id (str): ID транзакции

        Returns:
            Transaction: Модель отмененной транзакции
        """
        payload = build_query_payload(
            operation_name = "removeTransaction",
            query_key = "removeTransaction",
            variables = {
                "id": transaction_id
            }
        )
        
        response = await self.transport.request(
            method = "post",
            payload = payload
        )

        result = response.json().get("data", {}).get("removeTransaction")
        
        return Transaction.model_validate(result)


    async def request_withdrawal(
        self,
        provider: TransactionProviderIds,
        account: str,
        value: int,
        payment_method_id: Optional[TransactionPaymentMethodIds],
        sbp_bank_member_id: Optional[str]
    ) -> Transaction:
        """
        Создает запрос навывод средств с баланса аккаунта

        Args:
            provider (TransactionProviderIds): Провайдер транзакции
            account (str): ID добавленной карты (или номер телефона, если провайдер СБП), на которую нужно совершить вывод
            value (int): Сумма вывода
            payment_method_id (Optional[TransactionPaymentMethodIds]): ID платёжного метода
            sbp_bank_member_id (Optional[str]): ID члена банка СБП (только если указан провайдер СБП)

        Returns:
            Transaction: Модель транзакции вывода
        """

        payload = build_query_payload(
            operation_name = "requestWithdrawal",
            query_key = "requestWirequestWithdrawalthdrawal",
            variables = {
                "input": {
                    "provider": provider.name,
                    "account": account,
                    "value": value,
                    "providerData": {
                        "paymentMethodId": payment_method_id.name if payment_method_id else None,
                        "sbpBankMemberId": sbp_bank_member_id if sbp_bank_member_id else None
                    }
                }
            }
        )
        
        response = await self.transport.request(
            method = "post",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("requestWithdrawal")
        
        return Transaction.model_validate(result)