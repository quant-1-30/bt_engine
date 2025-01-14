#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import itertools
import datetime
from typing import Any, List
import numpy as np
from utils.dt_utilty import elapsed, str2dt, loc2dt
# from six import with_metaclass
from meta import ParamBase
from core.trade.commission import *
from core.trade.order import BaseOrder, Transaction
from .dist import *
from .restrict import Untradeable


class BtBroker(ParamBase):
    """
        impact_factor:  measure sim_vol should less than real tick volume
        slippage_factor: sim_price should multiplier real tick price
        epsilon: measure whether price reaches on limit always on the trading_day
        bid_mechnism: execute on time or price
    """
    params = (
        ("level", 1),
        ("delay", 2),
        ("impact_factor", 0.2),
        ("slippage_factor", 0.01),
        ("epsilon", 0.05),
        ("dist", "beta"),
        ("commission", "exchange"),
    )

    def __init__(self, kwargs):
        # exchanges: List[Exchange] = []
        self.delay = kwargs.pop("delay", self.p.delay)
        self.impact_factor = kwargs.pop("impact_factor", self.p.impact_factor) 
        self.slippage_factor = kwargs.pop("slippage_factor", self.p.slippage_factor) 
        self.commission = commission_factory[self.p.commission]
        self.restrict = Untradeable(kwargs.pop("epsilon", self.p.epsilon))

    async def _logical_deal(self, pos, downsamples, ord: BaseOrder) -> Transaction:
        ask_price = downsamples[0][pos + self.p.delay]
        fee_ratio = self.commission.calc_rate(ord)
        # slippage_price and slippage_vol
        slip_price = ask_price * ( 1 + self.slippage_factor) * (1 + fee_ratio)
        slip_vol = ord.calc_volume(slip_price) if ord.direction == 1 else ord.volume
        if slip_vol:
            # estimate impact on market
            tolerate_vol = downsamples[1][pos + self.p.delay] * self.p.impact
            filled_vol = slip_vol if slip_vol <= tolerate_vol else tolerate_vol

            # create transaction
            trade_cost = fee_ratio * filled_vol * slip_price
            transaction = Transaction(sid=ord.sid, 
                                      price=slip_price, 
                                      size=filled_vol, 
                                      cost=trade_cost)
            return transaction
        return ''
    
    async def _on_tick(self, ord: BaseOrder, downsamples) -> Transaction:
        seconds = elapsed(ord.created_dt)
        pos = int(np.ceil(seconds/3))
        txn = await self._logical_deal(pos, downsamples, ord)
        # set txn created_dt
        txn.created_dt = str2dt(ord.created_dt) + datetime.timedelta(seconds=self.p.delay) 
        return txn

    async def _on_price(self, ord: BaseOrder, downsamples) -> Transaction:
        locs = np.argwhere(downsamples[0] <= ord.price) if ord.direction == 1 else np.argwhere(downsamples[0] >= ord.price)
        if len(locs):
            txn = await self._logical_deal(locs[0][0], downsamples, ord)
            # set txn created_dt
            txn.created_dt = loc2dt(locs[0][0], ord.created_dt) + datetime.timedelta(seconds=self.p.delay)  
            return txn
        return ''
    
    def downsample(self, minutes):
        """
            m -> 3s tick
        """
        dist = dist_factory[self.p.dist]
        ticks = [dist.infer(snapshot) for snapshot in minutes]
        tick_prices = [item[0] for item in ticks]
        tick_vols = [item[1] for item in ticks]
        price_arrays = np.array(itertools.chain(*tick_prices))
        vol_arrays = np.array(itertools.chain(*tick_vols)) 
        return price_arrays, vol_arrays

    async def on_trade(self, order: BaseOrder, minutes: List[dict]) -> Transaction:
        """
        # orders to transactions
        Order event push.
        Order event of a specific vt_orderid is also pushed.
        """
        # np.logical_and(txn.match_price>=restricted.channel[0], txn.match_price<=restricted.channel[1]):
        restricted = self.restrict.is_restricted(order.asset, order.created_dt)
        if not restricted:
            downsamples = self.downsample(minutes)
            if order.order_type == 4:
                txn = await self._on_tick(order, downsamples)
            else:
                txn = await self._on_price(order, downsamples)
            return txn
        return ''
    