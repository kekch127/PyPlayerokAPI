# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator, Field
from typing import List, Optional, TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from .account import AccountProfile
    from .user import UserProfile

from ..types.enums import (
    TransactionPaymentMethodIds,
    TransactionProviderIds,
    TransactionOperations,
    TransactionDirections,
    TransactionStatuses
)

class TransactionPaymentMethod(BaseModel):
    # Платёжный метод транзакции

    id: TransactionPaymentMethodIds  # ID метода
    name: str # Название метода
    fee: int  # Комиссия метода
    provider_id: Optional[TransactionProviderIds] = None # ID провайдера транзакции
    account: Optional[AccountProfile] = None  # Аккаунт метода
    props: TransactionProviderProps  # Параметры провайдера
    limits: TransactionProviderLimits  # Лимиты провайдера
    
    # ===== ENUM CONVERTER =====
    @field_validator("id", mode = "before")
    @classmethod
    def convert_id(cls, v):
        if isinstance(v, str):
            return TransactionPaymentMethodIds[v]
        return v
    
    @field_validator("provider_id", mode = "before")
    @classmethod
    def convert_provider_id(cls, v):
        if isinstance(v, str):
            return TransactionProviderIds[v]
        return v

    class Config:
        populate_by_name = True



class TransactionProviderLimitRange(BaseModel):
    # Диапазон лимитов провайдера транзакции

    min: int # Минимальная сумма (в рублях)
    max: int # Максимальная сумма (в рублях)


class TransactionProviderLimits(BaseModel):
    # Лимиты провайдера транзакции

    incoming: TransactionProviderLimitRange  # На пополнение
    outgoing: TransactionProviderLimitRange  # На вывод
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_incoming(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        incoming = data.get("incoming")
        if incoming:
            data["incoming"] = incoming
        
        return data
    
    @model_validator(mode = "before")
    def transform_outgoing(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        outgoing = data.get("outgoing")
        if outgoing:
            data["outgoing"] = outgoing
        
        return data


    class Config:
        populate_by_name = True


class TransactionProviderRequiredUserData(BaseModel):
    # Обязательные пользовательские данные провайдера

    email: Optional[bool]  # Обязательно ли указывать email
    phone_number: Optional[bool] = Field(None, alias = "phoneNumber") # Обязательно ли указывать номер телефона
    erip_account_number: Optional[bool] = Field(None, alias = "eripAccountNumber") # Обязательно ли указывать номер ЕРИП


class TransactionProviderProps(BaseModel):
    # Параметры провайдера транзакции

    required_user_data: TransactionProviderRequiredUserData  # Обязательные пользовательские данные
    tooltip: Optional[str]  # Подсказка 
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_required_user_data(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        required_user_data = data.get("requiredUserData")
        if required_user_data:
            data["required_user_data"] =  required_user_data
        
        return data


    class Config:
        populate_by_name = True


class TransactionProvider(BaseModel):
    # Объект провайдера транзакции

    id: TransactionProviderIds # ID провайдера
    name: str  # Название провайдера
    fee: int  # Комиссия провайдера
    min_fee_amount: Optional[int] = Field(None, alias = "minFeeAmount") # Минимальная комиссия
    description: Optional[str] = Field(None, alias = "description")  # Описание провайдера
    account: Optional[AccountProfile] = None  # Аккаунт провайдера 
    props: TransactionProviderProps  # Параметры провайдера 
    limits: TransactionProviderLimits  # Лимиты провайдера 
    payment_methods: Optional[List[TransactionPaymentMethod]] = None # Платёжные методы 
    
    # ===== ENUM CONVERTER =====
    @field_validator("id", mode = "before")
    @classmethod
    def convert_id(cls, v):
        if isinstance(v, str):
            return TransactionProviderIds[v]
        return v
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_payment_methods(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        payment_methods = data.get("paymentMethods")
        if payment_methods:
            data["payment_methods"] = payment_methods 
        
        return data
    
    @model_validator(mode = "before")
    def transform_account_to_profile(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        profile = data.get("profile", {})
        if profile:
            merged = {**data, **profile}
            data["account"] = merged 
        
        return data


    class Config:
        populate_by_name = True


class Transaction(BaseModel):
    # Объект транзакции

    id: str  # ID транзакции
    operation: Optional[TransactionOperations] = None  # Тип операции
    direction: Optional[TransactionDirections] = None  # Направление транзакции
    provider_id: Optional[TransactionProviderIds] = None  # ID провайдера
    provider: Optional[TransactionProvider] = None  # Объект провайдера
    user: Optional[UserProfile] = None  # Пользователь транзакции
    creator: Optional[UserProfile] = None  # Создатель транзакции 
    status: Optional[TransactionStatuses] = None  # Статус обработки
    status_description: Optional[str] = Field(None, alias = "statusDescription")  # Описание статуса
    status_expiration_date: Optional[str] = Field(None, alias = "statusExpirationDate")  # Дата истечения статуса
    value: Optional[Union[int, float]] = 0  # Сумма транзакции
    fee: Optional[Union[int, float]] = 0  # Комиссия транзакции
    created_at: Optional[str] = Field(None, alias = "createdAt") # Дата создания
    verified_at: Optional[str] = None # Дата подтверждения
    verified_by: Optional[UserProfile] = None   # Кто подтвердил
    completed_at: Optional[str] = None  # Дата выполнения
    completed_by: Optional[UserProfile] = None  # Кто выполнил
    payment_method_id: Optional[str] = Field(None, alias = "paymentMethodId")  # ID способа оплаты
    is_suspicious: Optional[bool] = None  # Подозрительная транзакция
    sbp_bank_name: Optional[str] = Field(None, alias = "spb_bank_name") # Название банка СБП
    
    # ===== ENUM CONVERTER =====
    @field_validator("operation", mode = "before")
    @classmethod
    def convert_operation(cls, v):
        if isinstance(v, str):
            return TransactionOperations[v]
        return v
    
    @field_validator("direction", mode = "before")
    @classmethod
    def convert_direction(cls, v):
        if isinstance(v, str):
            return TransactionDirections[v]
        return v
    
    @field_validator("provider_id", mode = "before")
    @classmethod
    def convert_provider_id(cls, v):
        if isinstance(v, str):
            return TransactionProviderIds[v]
        return v
    
    @field_validator("status", mode = "before")
    @classmethod
    def convert_status(cls, v):
        if isinstance(v, str):
            return TransactionStatuses[v]
        return v


    class Config:
        populate_by_name = True


class TransactionPageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class TransactionList(BaseModel):
    transactions: Optional[List[Transaction]] = None # Транзакции страницы
    page_info: TransactionPageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount") 

    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_transactions(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        edges = data.get("edges")
        if edges:
            data["transactions"] = [transaction.get("node") for transaction in edges]
        
        return data


    class Config:
        populate_by_name = True