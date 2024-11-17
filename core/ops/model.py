#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from dataclasses import dataclass
from functools import total_ordering
from typing import List, Any, Dict, Union, Mapping
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


@dataclass(frozen=True, order=True)
class Experiment:

    user_id: str
    account_id: str
    experiment_id: str

    def serialize(self) -> dict:
        return {"user_id": self.user_id, "account_id": self.account_id, "experiment_id": self.experiment_id}


@dataclass(frozen=True, order=True)
class Order:

    order_id: str
    sid: int
    order_type: int
    created_dt: int
    order_price: int
    order_volume: int

    def serialize(self) -> dict:
        return {"order_id": self.order_id, "sid": self.sid, "order_type": self.order_type, 
                "created_at": self.created_at, "order_price": self.order_price, "order_volume": self.order_volume}
    

@dataclass(frozen=True, order=True)
class Transaction:

    sid: str
    created_at: int
    trade_price: int
    market_price: int
    volume: int
    cost: int

    def serialize(self) -> dict:
        return {"sid": self.sid, "created_at": self.created_at, "trade_price": self.trade_price, 
                "market_price": self.market_price, "volume": self.volume, "cost": self.cost}


@dataclass(frozen=True, order=True)
class Account:

    date: str
    positions: str
    portfolio: int
    cash: int

    def serialize(self) -> dict:
        return {"date": self.date, "positions": self.positions, 
                "portfolio": self.portfolio, "cash": self.cash}
