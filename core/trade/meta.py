#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Mapping
from pydantic import BaseModel, field_validator, Field


class AssetMeta(BaseModel):
    sid: str
    first_trading: int
    delist: int


class OrderMeta(BaseModel):
    asset: AssetMeta
    order_type: int
    direction: int
    price: int
    amount: int = Field(default=0)
    size: int = Field(default=0)

    @field_validator('direction')
    def validate_direction(cls, v):
        if v not in [1, 0]:
            raise ValueError('Invalid order type')
        return v

    class Config:
        extra = 'forbid'
        allow_mutation = False


class TransactionMeta(BaseModel):

    sid: str
    created_at: int
    trade_price: int
    market_price: int
    volume: int
    cost: int
    
    class Config:
        extra = 'forbid'
        allow_mutation = False

# @dataclass(frozen=True, order=True)
class AccountMeta(BaseModel):
    """
    The account object tracks information about the trading account. The
    values are updated as the algorithm runs and its keys remain unchanged.
    If connected to a broker, one can update these values with the trading
    account values as reported by the broker.
    """
    date: int
    positions: str
    portfolio: int
    balance: int

    class Config:
        extra = 'forbid'
        allow_mutation = False


class MetricsMeta(BaseModel):

    pnl: Mapping[str, float]
    usage: float
    portfolio_weight: Mapping[str, float]   

    class Config:
        extra = 'forbid'
        allow_mutation = False
