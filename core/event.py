#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from dataclasses import dataclass
from functools import total_ordering
from typing import List, Any, Dict, Union, Mapping
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from core.ops.model import Order, Transaction, Experiment


class Event(BaseModel):

    typ: str
    data: Any

    @field_validator("typ", mode="before")
    def restricted(cls, value):
        assert value in ("split", "dividend")
        return value


class TradeEvent(BaseModel):

    order: Order
    data: dict


class SyncEvent(BaseModel):

    session_ix: int
    data: Mapping[str, float]

    # class Config:
    #     date_encoders = {
    #         datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
    #     }


class QueryEvent(BaseModel):
     
     start: int
     end: int
     experiment_id: str


class LoginEvent(BaseModel):
     
     user_id: str
     accout_id: str
     token: str

     @field_validator("user_id", mode="before")
     def validate(cls, value):
          # re match
          return value
    
    
class RespEvent(BaseModel):
     
     status: int
     error: str


class PortfolioEvent(BaseModel):
        
        avaiable: float
        pnl: Mapping[str, float]
        usage: float
        portfolio_value: float
        portfolio_weight: Mapping[str, float]
