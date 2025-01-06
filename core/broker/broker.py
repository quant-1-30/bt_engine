
import datetime
import itertools
from textwrap import dedent
from typing import Any, List
import numpy as np
from utils.dt_utilty import elapsed, str2dt, loc2dt
# from six import with_metaclass
from meta import ParamBase
from core.trade.commission import Commission
from core.event import TradeEvent
from core.ops.model import Order, Transaction


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
        ("epsilon", 0.005),
    )

    def __init__(self, kwargs):
        # exchanges: List[Exchange] = []
        self.delay = kwargs.pop("delay", self.p.delay)
        self.impact_factor = kwargs.pop("impact_factor", self.p.impact_factor) 
        self.slippage_factor = kwargs.pop("slippage_factor", self.p.slippage_factor) 
        self.simulate = kwargs.pop("analog", "BetaPatch") 
        self.commission = Commission()

    def on_restricted(self, minutes):
        """
            订单设立可成交区间，涨跌幅有限制
            high - low < epison 由于st数据无法获取, 关于sid restricted 无法准确, 通过high / low 振幅判断
        """
        low = np.min(np.array([item["low"] for item in minutes]))
        high = np.max(np.array([item["high"] for item in minutes]))
        pct = (high - low)/low
        status = True if pct <= self.p.epsilon else False
        return status 

    async def yield_simulation(self, minutes):
        """
            patch minutes to 3 second tick
        """
        ticks = [self.tick_patch.patch(snapshot) for snapshot in minutes]
        tick_prices = [item[0] for item in ticks]
        tick_vols = [item[1] for item in ticks]
        price_arrays = np.array(itertools.chain(*tick_prices))
        vol_arrays = np.array(itertools.chain(*tick_vols)) 
        return price_arrays, vol_arrays
    
    async def _exec_deal(self, pos, simulations, order) -> Transaction:
        ask_price = simulations[0][pos + self.p.delay]
        fee_ratio = self.commission.calc_rate(order)
        # slippage_price and slippage_vol
        slip_price = ask_price * ( 1 + self.slippage_factor) * (1 + fee_ratio)
        slip_vol = order.on_validate(slip_price) if order.direction == 1 else order.volume
        if slip_vol:
            # estimate impact on market
            tolerate_vol = simulations[1][pos + self.p.delay] * self.p.impact
            filled_vol = slip_vol if slip_vol <= tolerate_vol else tolerate_vol

            # create transaction
            trade_cost = fee_ratio * filled_vol * slip_price
            transaction = Transaction(sid=order.sid, 
                                      price=slip_price, 
                                      size=filled_vol, 
                                      cost=trade_cost)
            return transaction
        return ''
    
    async def _on_tick(self, order:Order, downsamples) -> Transaction:
        seconds = elapsed(order.created_dt)
        pos = int(np.ceil(seconds/3))
        txn = await self._exec_deal(pos, downsamples, order)
        # set txn created_dt
        txn.created_dt = str2dt(order.created_dt) + datetime.timedelta(seconds=self.p.delay) 
        return txn

    async def _on_price(self, order:Order, downsamples) -> Transaction:
        locs = np.argwhere(downsamples[0] <= order.price) if order.direction == 1 else np.argwhere(downsamples[0] >= order.price)
        if len(locs):
            txn = await self._exec_deal(locs[0][0], downsamples, order)
            # set txn created_dt
            txn.created_dt = loc2dt(locs[0][0], order.created_dt) + datetime.timedelta(seconds=self.p.delay)  
            return txn
        return ''
    
    async def on_trade(self, event: TradeEvent) -> Transaction:
        """
        # orders to transactions
        Order event push.
        Order event of a specific vt_orderid is also pushed.
        """
        order = event.order
        minutes = event.data
        # np.logical_and(txn.match_price>=restricted.channel[0], txn.match_price<=restricted.channel[1]):
        restricted = self.on_restricted(minutes)
        txn = ''
        if not restricted:
            simulations = await self.yield_simulation(minutes)
            if order.order_type == 4:
                txn = await self._on_tick(order, simulations)
            else:
                txn = await self._on_price(order, simulations)
        return txn
