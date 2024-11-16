
import datetime
import itertools
from textwrap import dedent
from typing import Any, List
import numpy as np
from numpy.random import default_rng # type: ignore
from core.obj import Transaction, Commission, Order
from utils.dt_utilty import elapsed, str2dt, loc2dt
# from six import with_metaclass
from meta import ParamBase


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
        self.downsample = kwargs.pop("analog", "Beta") 
        self.restricted = kwargs.pop("epsilon", self.p.restricted) 
        self.commission = Commission(self.p.base_cost, self.p.multiply)

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

    def analog(self, lines):
        """
            downsample 3/s tick price with 1/m price
        """
        vols = [item["volume"] for item in lines]
        tick_prices = [self.downsample.sample(tick)  for tick in lines]
        tick_vols = [self.downsample.sample(vol)  for vol in vols]
        price_arrays = np.array(itertools.chain(*tick_prices))
        vol_arrays = np.array(itertools.chain(*tick_vols)) 
        return price_arrays, vol_arrays
    
    def _on_deal(self, anchor, samples, order):
        # slippage_price
        fee = self.commission.calc_rate(order)
        slippage_price = samples[0][anchor + self.p.delay] * ( 1 + self.slippage_factor) * (1 + fee)
        slippage_vol = order.on_validate(slippage_price) if order.direction == 1 else order.volume
        if slippage_vol:
            # estimate impact on market
            market_impact_vol = samples[1][anchor + self.p.delay] * self.p.impact
            filled_vol = slippage_vol if slippage_vol <= market_impact_vol else market_impact_vol

            # create transaction
            trade_cost = fee * filled_vol * slippage_price
            transaction = Transaction(sid=order.sid, 
                                      price=slippage_price, 
                                      size=filled_vol, 
                                      cost=trade_cost)
            return transaction
        return ''
    
    def trigger_on_dt(self, order, downsamples):
        seconds = elapsed(order.created_dt)
        anchor = int(np.ceil(seconds/3))
        txn = self._on_deal(anchor, downsamples, order)
        # set txn created_dt
        txn.created_dt = str2dt(order.created_dt) + datetime.timedelta(seconds=self.p.delay) 
        return txn

    def trigger_on_price(self, order, downsamples):
        anchors = np.argwhere(downsamples[0] <= order.price) if order.direction == 1 else np.argwhere(downsamples[0] >= order.price)
        if len(anchors):
            txn = self._on_deal(anchors[0][0], downsamples, order)
            # set txn created_dt
            txn.created_dt = loc2dt(anchors[0][0], order.created_dt) + datetime.timedelta(seconds=self.p.delay)  
            return txn
        return ''
    
    def on_trade(self, order, minutes) -> None:
        """
        # orders to transactions
        Order event push.
        Order event of a specific vt_orderid is also pushed.
        """
        # np.logical_and(txn.match_price>=restricted.channel[0], txn.match_price<=restricted.channel[1]):
        restricted = self.on_restricted(minutes)
        txn = ''
        if not restricted:
            downsamples = self.analog(minutes)
            # estimate order volume 
            if order.order_type == 4:
                txn = self.trigger_on_dt(order, downsamples)
            else:
                txn = self.trigger_on_price(order, downsamples)
        return txn
