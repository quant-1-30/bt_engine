# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
from dataclasses import dataclass
import pandas as pd
from core.event import Order


@dataclass
class Commission:

    base_cost: int = 5
    multiply: int = 5

    def patch(self, order):

        raise NotImplementedError()
    
    def calc_rate(self, order):
        fee_ratio = self.patch(order=order)
        return fee_ratio
    

class NoCommission(Commission):

    def patch(self, order):
        return 0.0
    

class Exchange(Commission):

    def patch(self, order: Order):
       # 印花税 1‰(卖的时候才收取，此为国家税收，全国统一)
        stamp_rate = 0 if order.direction== 1 else 1e-3
        # 过户费：深圳交易所无此项费用，上海交易所收费标准(按成交金额的0.02)
        transfer_rate = 2 * 1e-5 if order.sid.startswith('6') else 0
        # struct_date = datetime.datetime.fromtimestamp(transaction.created_dt).strftime("%Y%m%d")
        # 交易佣金：最高收费为3‰, 2015年之后万/3
        benchmark = 1e-4 if order.created_dt > pd.Timestamp('2015-06-09') else 1e-3
        # 完整的交易费率
        per_rate = stamp_rate + transfer_rate + benchmark * self.multiplier 
        return per_rate
