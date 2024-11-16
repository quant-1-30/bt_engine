#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from copy import copy
import numpy as np
import pandas as pd
from toolz import valmap
from collections import defaultdict, OrderedDict
from functools import partial
from position import Position
from utils.wrapper import _deprecated_getitem_method


class MutableView(object):
    """A mutable view over an "immutable" object.

    Parameters
    ----------
    ob : any
        The object to take a view over.
    """
    # add slots so we don't accidentally add attributes to the view instead of
    # ``ob``
    # __slots__ = ['_mutable_view_obj']

    def __init__(self, ob):
        object.__setattr__(self, '_mutable_view_obj', ob)

    def __getattr__(self, item):
        return getattr(self._mutable_view_ob, item)

    def __setattr__(self, attr, value):
        # vars() 函数返回对象object的属性和属性值的字典对象 --- 扩展属性类型 ,不改变原来的对象属性
        vars(self._mutable_view_ob)[attr] = value

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._mutable_view_ob)


class Position(object):

    __slots__ = ['inner_position', '_position_daily_returns', '_closed']

    def __init__(self,
                 sid,
                 size=0,
                 price=0.0):

        # # 属性只能在inner里面进行更新 --- 变相隔离
        # inner = InnerPosition(
        #         sid=sid,
        #         size=size,
        #         cost_basis=cost_basis,
        #         last_sync_price=last_sync_price,
        #         last_sync_date=last_sync_date,
        #         position_returns=pd.Series(dtype='float64')
        # )
        # self.inner_position = inner
        self.size = size
        if size:
            self.price = self.cost_basis = price
        else:
            self.price = self.cost_basis = 0.0
        self.upopened = size
        self.upclosed = 0
        # intraday
        self.avaiable = 0
        self.intraday = False
    
    def __len__(self):
        return abs(self.size)

    def __bool__(self):
        return bool(self.size != 0)

    # In Python 3, __nonzero__() was renamed to __bool__()
    __nonzero__ = __bool__

    def clone(self):
        return Position(sid=self.sid, size=self.size, price=self.price)

    def __getattr__(self, item):
        return getattr(self.inner_position, item)

    def on_splits(self, size_ratio=1.0, bonus_ratio=0.0):
        """
            update the postion by the split ratio and return the fractional share that will be converted into cash (除权）
            零股转为现金 ,重新计算成本,
            散股 -- 转为现金
        """
        #ZeroDivisionError异常和RuntimeWarning警告之间的区别 --- numpy.float64类型(RuntimeWarning) 稳健方式基于0判断
        oldsize = self.size
        self.size = oldsize * size_ratio
        self.cost_basis = round(self.cost_basis / size_ratio, 2)
        bonus = oldsize * bonus_ratio
        return bonus
    
    def on_rights(self):
        pass

    def on_update(self, txn):
        '''
        Updates the current position and returns the updated size, price and
        units used to open/close a position

        Args:
            size (int): amount to update the position size
                size < 0: A sell operation has taken place
                size > 0: A buy operation has taken place

            price (float):
                Must always be positive to ensure consistency

        Returns:
            A tuple (non-named) contaning
               size - new position size
                   Simply the sum of the existing size plus the "size" argument
               price - new position price
                   If a position is increased the new average price will be
                   returned
                   If a position is reduced the price of the remaining size
                   does not change
                   If a position is closed the price is nullified
                   If a position is reversed the price is the price given as
                   argument
               opened - amount of contracts from argument "size" that were used
                   to open/increase a position.
                   A position can be opened from 0 or can be a reversal.
                   If a reversal is performed then opened is less than "size",
                   because part of "size" will have been used to close the
                   existing position
               closed - amount of units from arguments "size" that were used to
                   close/reduce a position

            Both opened and closed carry the same sign as the "size" argument
            because they refer to a part of the "size" argument
        '''
        self.datetime = txn.created_dt  # record datetime update (datetime.datetime)

        self.price_orig = self.price
        oldsize = self.size
        self.size += txn.size

        if not self.size:
            # Update closed existing position
            opened, closed = 0, txn.size
            self.price = 0.0
        elif not oldsize:
            # Update opened a position from 0
            opened, closed = txn.size, 0
            self.price = txn.price
        elif oldsize > 0:  # existing "long" position updated

            if txn.size > 0:  # increased position
                opened, closed = txn.size, 0
                self.price = self.cost_basis = (self.price * oldsize + txn.size * txn.price) / self.size

            elif self.size > 0:  # reduced position
                opened, closed = 0, txn.size
                # self.price = self.price
                self.cost_basis = self.price - txn.size * (txn.price - self.price) / oldsize

            else:  # self.size < 0 # reversed position form plus to minus
                raise NotImplementedError("not supported short positon ops")

        else:  # oldsize < 0 - existing short position updated
            raise NotImplementedError("not supported short sale")

        self.upopened += opened
        self.upclosed += closed

        self.on_intraday()

    def on_intraday(self):
        # T+1
        self.size += self.upopened
        self.size -= self.upclosed
        if not self.intraday:
            self.avaiable -= self.upclosed
        else:
            self.on_sync()
    
    @property
    def closed(self):
        return self.size == 0

    def on_sync(self, close):
        # end of trading day
        self.avaiable = self.size.copy()
        self.price = close

    def __repr__(self):
        template = "Position(sid={sid}," \
                   "size={size}," \
                   "price={price}"
        return template.format(
            sid=self.sid,
            size=self.size,
            price=self.cost_basis,
        )
    
    def __str__(self):
        items = list()
        items.append('--- Position Begin')
        items.append('- Size: {}'.format(self.size))
        items.append('- Price: {}'.format(self.price))
        items.append('- Cost_basis: {}'.format(self.cost_basis))
        items.append('- Closed: {}'.format(self.upclosed))
        items.append('- Opened: {}'.format(self.upopened))
        items.append('--- Position End')
        return '\n'.join(items)

    def to_dict(self):
        """
            create a dict representing the state of this position
        """
        return {
            'sid': self.sid,
            'size': self.size,
            'price': self.price,
            }
    

class PositionTracker(object):
    """
        track the change of position
    """
    def __init__(self):
        self.positions = OrderedDict()
        self.record_closed_position = defaultdict(list)
        self._dirty_stats = True

    @staticmethod
    def _calc_ratio(dividend):
        """
            股权登记日 ex_date
            股权除息日（为股权登记日下一个交易日）
            但是红股的到账时间不一致（制度是固定的）
            根据上海证券交易规则,对投资者享受的红股和股息实行自动划拨到账。股权(息)登记日为R日,除权(息)基准日为R+1日
            投资者的红股在R+1日自动到账, 并可进行交易,股息在R+2日自动到帐
            其中对于分红的时间存在差异
            根据深圳证券交易所交易规则,投资者的红股在R+3日自动到账,并可进行交易,股息在R+5日自动到账
            持股超过1年 税负5%; 持股1个月至1年 税负10%; 持股1个月以内 税负20%新政实施后,上市公司会先按照5%的最低税率代缴红利税
        """
        try:
            size_ratio = (dividend['sid_bonus'] + dividend['sid_transfer']) / 10
            bonus_ratio = dividend['bonus'] / 10
        except ZeroDivisionError:
            size_ratio = 1.0
            bonus_ratio = 0.0
        return size_ratio, bonus_ratio

    def _on_splits(self, dividends):
        total_bonus = 0
        for sid, p_obj in self.positions.items():
            # update last_sync_date
            try:
                dividend = dividends.loc[sid, :]
                ratio = self._calc_ratio(dividend)
                bonus = p_obj.on_splits(*ratio)
                total_bonus += bonus
            except KeyError:
                pass
        return total_bonus
    
    def _on_rights(self, rights):
        """
            配股机制如果不缴纳款，自动放弃到期除权相当于亏损,在股权登记日卖出 一般的配股缴款起止日为5个交易日
        """
        return 0.0

    def process_event(self, event):
        if event.typ == "splits":
            data = self._on_splits(event)
        else:
            data = self._on_rights(event)
        return data

    def update(self, transactions):
        for txn in transactions:
            sid = txn.sid
            try:
                position = self.positions[sid]
            except KeyError:
                position = self.positions[sid] = Position(sid)
        
            position.on_update(txn)
            print("position ", position)
            if position.closed:
                dts = txn.created_dt.strftime('%Y-%m-%d')
                self.record_closed_position[dts].append(position)
                print('end session closed positions', self.record_closed_position)
                del self.positions[sid]

    def on_sync(self, prices):
        """
            a. sync last_sale_price of position (close price)
            b. update position return series
            c. update last_sync_date
        including : positions and closed position
        """
        for p_obj in self.positions.values():
            p_obj.on_sync(prices[p_obj.sid])

    def get_positions(self):
        # return protocol mappings
        protocols = valmap(lambda x: x.to_dict(), self.positions)
        return protocols
