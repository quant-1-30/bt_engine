
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
from abc import ABC, abstractmethod
from core.const import OrderType, OrderStatus
from .meta import OrderMeta
from .asset import Asset


class BaseOrder(ABC):

    # self.direction = math.copysign(1, size) if size else math.copysign(1, amount)

    def update_status(self, status):
        self._status = status

    @abstractmethod
    def calc_volume(self, price):
        raise NotImplementedError
    

class PutOrder(BaseOrder):
    
    # using __slots__ to save on memory usage to cut down on the memory footprint of this object.
    __slots__ = ["asset", "size", "price", "order_type", "created_dt", "_status"]
    
    def __init__(self, asset: Asset, size: int=0, price: int=0, created_dt='', order_type=OrderType.Market, status=OrderStatus.OPEN):
        self.asset = asset
        self.size = size
        self.price = price
        self.order_type = order_type
        self.created_dt = created_dt
        self._status = status

    def calc_volume(self, price=0.0):
        return self.size
    
    def __repr__(self):
        return f"PutOrder(asset={self.asset}, size={self.size}, price={self.price}, order_type={self.order_type}, created_dt={self.created_dt}, status={self._status})"


class CallOrder(BaseOrder):
    
    # using __slots__ to save on memory usage to cut down on the memory footprint of this object.
    __slots__ = ["asset", "amount", "price", "order_type", "created_dt", "_status"]
    
    def __init__(self, asset: Asset, amount: int=0, price: int=0, created_dt='', order_type=OrderType.Market, status=OrderStatus.OPEN ):
        self.asset = asset
        self.amount = amount
        self.price = price
        self.order_type = order_type
        self.created_dt = created_dt
        self._status = status

    def calc_volume(self, price):
        """
            estimeate size based on policy
        """
        incr =  200 if self.sid.startswith("688") else 100 
        per_value = incr * price
        approximate = 0 if per_value > self.amount else incr * (self.amount // price)
        return approximate
    
    def __repr__(self):
        return f"CallOrder(asset={self.asset}, amount={self.amount}, price={self.price}, order_type={self.order_type}, created_dt={self.created_dt}, status={self._status})"


class Transaction(object):

    __slots__ = ['sid', 'amount', 'price', 'created_dt', 'cost']

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


def create_order(order_meta: OrderMeta):
    if order_meta.direction:
        asset = Asset(**order_meta.asset.model_dump())
        return PutOrder(asset, order_meta.size, order_meta.price, order_meta.created_dt, order_meta.order_type, order_meta.status)
    else:
        return CallOrder(order_meta.sid, order_meta.amount, order_meta.price, order_meta.created_dt, order_meta.order_type, order_meta.status)

