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
from deprecated import deprecated
from warnings import warn
from toolz import valmap
from typing import Mapping, Any, List
from collections import defaultdict, OrderedDict
from functools import partial
from utils.wrapper import _deprecated_getitem_method
from .meta import TransactionMeta   
from core.event import EquityEvent


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
        self.sid = sid
        self.size = size
        self.cost_basis = price
        self.avaiable = 0
        self.last_sync_date = 0

        # stats
        self.upopened = 0
        self.upclosed = 0
    
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

    def on_dividends(self, size_ratio=1.0, bonus_ratio=0.0):
        """
            update the postion by the split ratio and return the fractional share that will be converted into cash (除权）
        """
        #ZeroDivisionError异常和RuntimeWarning警告之间的区别 --- numpy.float64类型(RuntimeWarning) 稳健方式基于0判断
        oldsize = self.size
        self.size = oldsize * size_ratio
        self.cost_basis = round(self.cost_basis / size_ratio, 2)
        bonus = oldsize * bonus_ratio
        return bonus
    
    async def on_update(self, txn: TransactionMeta):
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

        oldsize = self.avaiable.copy()
        self.avaiable += txn.size

        assert self.avaiable >= 0, "not supported short position"

        if not self.avaiable:
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
                self.cost_basis = (self.price * oldsize + txn.size * txn.price) / (oldsize + txn.size)

            else:
                # self.avaiable > 0 reduced position
                opened, closed = 0, txn.size
                self.cost_basis = (self.price * oldsize - txn.size * txn.price) / (oldsize - txn.size)

        else:  # oldsize < 0 - existing short position updated
            raise NotImplementedError("not supported short sale")

        # stats
        self.upopened += opened
        self.upclosed += closed

    def on_last_sync(self, close: float, dt: int):
        # due to T+1 / end of trading day                 
        self.size += self.upopened
        self.size -= self.upclosed
        self.avaiable = self.size.copy()
        self.price = close
        self.upopened = 0
        self.upclosed = 0
        self.last_sync_date = dt
    
    @property
    def closed(self):
        return self.size == 0

    def __repr__(self):
        template = "Position(sid={sid}," \
                   "size={size}," \
                   "price={price}"
        return template.format(
            sid=self.sid,
            size=self.size,
            price=self.cost_basis,
        )
    
    def serialize(self):
        """
            create a dict representing the state of this position
        """
        return {
            'sid': self.sid,
            'size': self.size,
            'price': self.cost_basis,
            'avaiable': self.avaiable,
            }
    def __str__(self):
        items = list()
        items.append('--- Position Begin')
        items.append('- Sid: {}'.format(self.sid))
        items.append('- Size: {}'.format(self.size))
        items.append('- Price: {}'.format(self.cost_basis))
        items.append('- Avaiable: {}'.format(self.avaiable))
        items.append('- Closed: {}'.format(self.upclosed))
        items.append('- Opened: {}'.format(self.upopened))
        items.append('--- Position End')
        return '\n'.join(items)
   

class PositionTracker(object):
    """
        track the change of position
    """
    def __init__(self):
        self.positions = OrderedDict()
        self.record_closed_position = defaultdict(list)
        self._dirty_stats = True

    @staticmethod
    def _calc_ratio(dividend: Mapping[str, Any]):
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

    async def _on_split(self, dividends: Mapping[str, Any]):
        total_bonus = 0
        if dividends:
            for sid, p_obj in self.positions.items():
                try:
                    ratio = self._calc_ratio(dividends[sid])
                    bonus = p_obj.on_dividends(*ratio)
                    total_bonus += bonus
                except KeyError:
                    pass
        return total_bonus
    
    @deprecated(reason="right will be deprecated in the future , use position on_update instead")
    async def _on_right(self, rights: Mapping[str, Any]):
        """
            配股机制如果不缴纳款，自动放弃到期除权相当于亏损,在股权登记日卖出 一般的配股缴款起止日为5个交易日
        """
        warn("best practice is to use position on_update instead", UserWarning)

    async def process_event(self, event: EquityEvent):
        if event.event_type == "split":
            data = await self._on_split(event.meta)
        else:
            data = await self._on_right(event.meta)
        return data

    async def update(self, txns: List[TransactionMeta]):
        for txn in txns:
            sid = txn.sid
            try:
                position = self.positions[sid]
            except KeyError:
                position = self.positions[sid] = Position(sid)
        
            await position.on_update(txn)
            print("position ", position)
            if position.closed:
                dts = txn.created_dt.strftime('%Y-%m-%d')
                self.record_closed_position[dts].append(position)
                print('end session closed positions', self.record_closed_position)
                del self.positions[sid]

    async def syncronize(self, prices: Mapping[str, float], dt: int):
        """
            a. sync last_sale_price of position (close price)
            b. update position return series
            c. update last_sync_date
        including : positions and closed position
        """
        # update last_sync_date
        for p_obj in self.positions.values():
            await p_obj.on_last_sync(prices[p_obj.sid], dt)

    def _cleanup_expired(self, dt: int):
        """
            Clear out any assets that have expired before starting a new sim day.

            Finds all assets for which we have positions and generates
            close_position events for any assets that have reached their
            close_date.
        """
        def past_close_date(asset):
            acd = asset.delist
            return acd is not None and acd == dt
    
        # Remove positions in any sids that have reached their auto_close date.
        for p in self.positions.values():
            if p.size == 0 or past_close_date(p.sid):
                self.positions.pop(p.sid)           

    def get_positions(self):
        # return protocol mappings
        protocols = valmap(lambda x: x.to_dict(), self.positions)
        return protocols
