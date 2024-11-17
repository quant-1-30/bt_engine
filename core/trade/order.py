
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
import pdb
import pickle
import datetime
import numpy as np
import pandas as pd
import uuid
import math
from typing import List, Any, Dict, Union
from enum import Enum
from copy import copy
from meta import BaseObject


class OrderType(Enum):

    # lmt / fok / fak
    LIMIT = 1 << 1
    Market = 1 << 2


class OrderStatus(Enum):

    OPEN = 1
    FILLED = 2
    CANCELLED = 3
    REJECTED = 4
    HELD = 5
    SUBMITTING = 6


class Order(BaseObject):

    # using __slots__ to save on memory usage to cut down on the memory footprint of this object.
    
    __slots__ = ("created_dt", "sid", "amount", "size", "price", "direction", "order_type", "_status")

    # @expect_types(asset=Asset)
    def __init__(self, sid: str, order_type: int, price: int=0, amount: int=0, size: int=0, created_dt=''):

        """
            @dt - datetime.datetime that the order was placed
            @asset - asset for the order.
            @amount - the number of shares to buy/sell
                    a positive sign indicates a buy
                    a negative sign indicates a sell
            @filled - how many shares of the order have been filled so far
            @order_type: market / price
            @direction: 0 (buy) / 1 (sell)
        """
        self.sid = sid
        # 限价单 以等于或者低于限定价格买入 / 等于或者高于限定价格卖出订单 
        self.direction = math.copysign(1, size) if size else math.copysign(1, amount)
        self.amount = amount
        self.size = size
        self.price = price
        self.order_type = OrderType.Market
        self.created_dt = created_dt
        # get a string representation of the uuid.
        self.order_id = uuid.uuid4().hex
        self._status = OrderStatus.OPEN

    def on_status(self, status):
        self._status = status

    def calc_volume(self, price):
        """
            estimate volume threshold based on price and market
        """
        incr =  200 if self.sid.startswith("688") else 100 
        per_value = incr * price
        approximate = 0 if per_value > self.amount else incr * (self.amount // price)
        return approximate


class Transaction(object):

    __slots__ = ('sid', 'amount', 'price', 'created_dt', 'cost')

    def __init__(self,
                 sid: str,
                 size: str,
                 price: str,
                 cost: int,
                 created_dt: str=''):
        self.sid = sid
        self.size = size
        self.price = price
        self.created_dt = created_dt
        self.cost = cost

    def __repr__(self):
        template = (
            "{cls}(sid={sid},size={size},"
            "created_dt={created_dt},price={price},cost={cost})"
        )
        return template.format(
            cls=type(self).__name__,
            sid=self.sid,
            size=self.size,
            price=self.price,
            created_dt=self.created_dt,
            cost=self.cost
        )

    def __getitem__(self, attr):
        return self.__slots__[attr]

    def __getstate__(self):
        """
            pickle dumps
        """
        p_dict = {name: getattr(self, name) for name in self.__slots__}
        return p_dict


# from abc import ABC, abstractmethod
# from functools import lru_cache


# class ExecutionStyle(ABC):
#     """
#         Base class for order execution styles.
#         (stop_reached, limit_reached).
#         For market orders, will return (False, False).
#         For stop orders, limit_reached will always be False.
#         For limit orders, stop_reached will always be False.
#         For stop limit orders a Boolean is returned to flag
#         that the stop has been reached.
#     """
#     @staticmethod
#     @lru_cache(maxsize=32)
#     def get_pre_close(asset, dt):
#         """
#         """

#     @abstractmethod
#     def get_limit_ratio(self, asset, dts):
#         """
#         Get the limit price ratio for this order.
#         Returns either None or a numerical value >= 0.
#         """
#         raise NotImplementedError

#     @abstractmethod
#     def get_stop_ratio(self, asset, dts):
#         """
#         Get the stop price for this order.
#         Returns either None or a numerical value >= 0.
#         """
#         raise NotImplementedError


# class MarketOrder(ExecutionStyle):
#     """
#     Execution style for orders to be filled at current market price.

#     This is the default for orders placed with :func:`~zipline.api.order`.
#     """
#     def get_limit_ratio(self, asset, dts):
#         pre_close = super().get_pre_close(asset, dts)
#         limit_price = pre_close * (1 + asset.restricted_change(dts))
#         return limit_price

#     def get_stop_ratio(self, asset, dts):
#         pre_close = super().get_pre_close(asset, dts)
#         stop_price = pre_close * (1 - asset.restricted_change(dts))
#         return stop_price


# class LimitOrder(ExecutionStyle):
#     """
#     Execution style for orders to be filled at a price equal to or better than
#     a specified limit price.

#     Parameters
#     ----------
#     limit_price : float
#         Maximum price for buys, or minimum price for sells, at which the order
#         should be filled.
#     """
#     def __init__(self, limit):
#         self.limit = limit

#     def get_limit_ratio(self, asset, dts):
#         pre_close = super().get_pre_close(asset, dts)
#         limit_price = pre_close * (1 + self.limit)
#         return limit_price

#     def get_stop_ratio(self, asset, dts):
#         pre_close = super().get_pre_close(asset, dts)
#         stop_price = pre_close * (1 - asset.restricted_change(dts))
#         return stop_price


# class StopOrder(ExecutionStyle):
#     """
#     Execution style representing a market order to be placed if market price
#     reaches a threshold.

#     Parameters
#     ----------
#     stop_price : float
#         Price threshold at which the order should be placed. For sells, the
#         order will be placed if market price falls below this value. For buys,
#         the order will be placed if market price rises above this value.
#     """
#     def __init__(self, stop=0.07):
#         self.stop = stop

#     def get_limit_ratio(self, asset, dts):
#         pre_close = super().get_pre_close(asset, dts)
#         limit_price = pre_close * (1 + asset.restricted_change(dts))
#         return limit_price

#     def get_stop_ratio(self, asset, dts):
#         pre_close = super().get_pre_close(asset, dts)
#         stop_price = pre_close * (1 - self.stop)
#         return stop_price


# class StopLimitOrder(ExecutionStyle):
#     """
#     Execution style representing a limit order to be placed if market price
#     reaches a threshold.

#     Parameters
#     ----------
#     limit_price : float
#         Maximum price for buys, or minimum price for sells, at which the order
#         should be filled, if placed.
#     stop_price : float
#         Price threshold at which the order should be placed. For sells, the
#         order will be placed if market price falls below this value. For buys,
#         the order will be placed if market price rises above this value.
#     """
#     def __init__(self, kwargs):
#         self.limit = kwargs.get('limit', 0.08)
#         self.stop = kwargs.get('stop', 0.07)

#     def get_limit_ratio(self, asset, dts):
#         pre_close = super().get_pre_close(asset, dts)
#         limit_price = pre_close * (1 + self.limit)
#         return limit_price

#     def get_stop_ratio(self, asset, dts):
#         pre_close = super().get_pre_close(asset, dts)
#         stop_price = pre_close * (1 - self.stop)
#         return stop_price