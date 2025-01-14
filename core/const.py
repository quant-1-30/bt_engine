# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
from enum import Enum


class OrderType(Enum):
    # 限价单 以等于或者低于限定价格买入 / 等于或者高于限定价格卖出订单 

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

BEFORE_TRADING_START = 1
SESSION_START = 2
SESSION_END = 3

MAX_MONTH_RANGE = 23
MAX_WEEK_RANGE = 5

DEFAULT_DELAY_BASE = 1
DEFAULT_CAPITAL_BASE = 1e5
DEFAULT_PER_CAPITAL_BASE = 2e4
