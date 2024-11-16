# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Any, Dict, Union, Mapping
from datetime import datetime
from pydantic import BaseModel, field_validator


class ReqEvent(BaseModel):

    token: str
    sid: str
    typ: str
    amount: float = 0.0
    size: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

    @field_validator("typ")
    def restricted(cls):
        assert cls.typ in ("market", "price")

    @field_validator("sid")
    def restricted(cls):
        """
            6/0/3/688
            15/55
        """
        return True
    

class RespEvent(BaseModel):
     
     status: int
     id: str


class LoginEvent(BaseModel):
     
     user_id: str
     phone: str
     accout_id: str

     @field_validator("phone")
     def validate(cls):
          """
            re match phone 11 / 86 开头
          """
          return True


class AssetEvent(BaseModel):

    sid: str
    typ: str
    body: Any

    @field_validator("typ")
    def restricted(cls):
        assert cls.typ in ("splits", "dividends")


class PortfolioEvent(BaseModel):
        
        avaiable: float
        pnl: Mapping[str, float]
        usage: float
        portfolio_value: float
        portfolio_weight: Mapping[str, float]

