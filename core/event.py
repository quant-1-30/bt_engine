#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from typing import List, Any, Dict, Union, Mapping
from pydantic import BaseModel, field_validator
from core.trade.meta import OrderMeta


class LoginEvent(BaseModel):
     
     name: str
     phone: int
     email: str
     auto_register: bool = True

     @field_validator("phone", mode="before")
     def validate_phone(cls, value):
          # re match
          return value
     

class TradeEvent(BaseModel):

    orderMeta: OrderMeta
    payload: dict
    token: str
    experiment_id: str

    
class EquityEvent(BaseModel):

    event_type: str
    meta: Any
    token: str
    experiment_id: str

    @field_validator("event_type", mode="before")
    def restricted(cls, value):
        assert value in ("split", "dividend")
        return value


class SyncEvent(BaseModel):

    session_ix: int
    meta: Mapping[str, float]
    token: str
    experiment_id: str

    # class Config:
    #     date_encoders = {
    #         datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
    #     }

class MetricEvent(BaseModel):

    start_dt: int
    end_dt: int
    token: str
    experiment_id: str


class RespEvent(BaseModel):
     
     status: int
     error: str


__all__ = ["LoginEvent", "TradeEvent", "EquityEvent", "SyncEvent", "RespEvent"]
