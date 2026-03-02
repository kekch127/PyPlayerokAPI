# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, Any, Optional

from .types.queries import PERSISTED_QUERIES, QUERIES


def build_query_payload(
    operation_name: str,
    query_key: str,
    variables: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Формирует обычный GraphQL payload (через query).
    """

    return {
        "operationName": operation_name,
        "query": QUERIES.get(query_key),
        "variables": variables or {},
    }


def build_persisted_query_payload(
    operation_name: str,
    hash_key: str,
    variables: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Формирует GraphQL payload через persistedQuery (sha256Hash).
    """

    return {
        "operationName": operation_name,
        "variables": variables or {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": PERSISTED_QUERIES.get(hash_key),
            }
        },
    }
