
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
import pandas as pd
from toolz import valmap, keymap, merge_with
from typing import List
from core.trade.position import PositionTracker
from core.broker.broker import BtBroker
from core.event import Event, TradeEvent, SyncEvent, PortfolioEvent
from core.const import DEFAULT_CAPITAL_BASE


class Account(object):
    """
    The account object tracks information about the trading account. The
    values are updated as the algorithm runs and its keys remain unchanged.
    If connected to a broker, one can update these values with the trading
    account values as reported by the broker.
    """
    __slots__ = ('balance', 'portfolio')

    def __init__(self, balance, portfolio):
        self.balance = balance
        self.portfolio = portfolio

    def __repr__(self):
        return "Account({0})".format(self.__dict__)

    # def __setattr__(self, attr, value):
    #     raise AttributeError('cannot mutate Portfolio objects')


class Portfolio(object):
    """Object providing read-only access to current portfolio state.

    Parameters
    ----------
    capital_base : float
        The starting value for the portfolio. This will be used as the starting
        cash, current cash, and portfolio value.

    positions : Position object or None
        Dict-like object containing information about currently-held positions.

    """
    __slots__ = ['initial_balance', 'pnl', 'portfolio_daily_value']

    def __init__(self, balance):
        self.initial_balance = balance
        self.portfolio_daily_value = pd.Series(dtype='float64')
        self.pnl = pd.Series(dtype="float64")

    def calc_portfolio(self, session_ix, positions):
        portfolio_value = sum([p["price"] * p["size"] for p in positions])
        self.portfolio_daily_value[session_ix] = portfolio_value
        pnl = valmap(lambda p: p["price"] / p["cost_basis"] -1 , positions)
        self.pnl[session_ix] = pnl
        return portfolio_value, pnl, portfolio_value / self.balance

    def current_portfolio_weights(self, positions):
        """
        Compute each asset's weight in the portfolio by calculating its held
        value divided by the total value of all positions.

        Each equity's value is its price times the number of shares held. Each
        futures contract's value is its unit price times number of shares held
        times the multiplier.
        """
        if self.positions:
            p_objs = valmap(lambda p:  p.price * p.size, positions)
            aggregate = sum(p_objs.values())
            weights = pd.Series(p_objs) / aggregate
        else:
            weights = pd.Series(dtype='float')
        return weights.to_dict()

    # If you are adding new attributes, don't update this set. This method
    # is deprecated to normal attribute access so we don't want to encourage
    # new usages.
    # __getitem__ = _deprecated_getitem_method(
    #     'portfolio', {
    #         'capital_base',
    #         'portfolio_value',
    #         'pnl',
    #         'returns',
    #         'cash',
    #         'positions',
    #         'utility'
    #     },
    # )
    
    # def __repr__(self):
    #     return "Portfolio(Balance={portfolio_value}," \
    #            "positions_values={positions_values}".\
    #         format(portfolio_value=self.portfolio_value,
    #                positions_values=self.positions_values)


class Ledger(object):
    """
        the ledger tracks all orders and transactions as well as the current state of the portfolio and positions
        position_tracker 
    """
    def __init__(self, kwargs={}):        
        self.position_tracker = PositionTracker()
        self._broker = BtBroker(kwargs)
        balance = kwargs.get("initial_balance", DEFAULT_CAPITAL_BASE)
        self.portfolio = Portfolio(balance)
        self.avaiable = balance
    
    def getbroker(self):
        '''
        Returns the broker instance.

        This is also available as a ``property`` by the name ``broker``
        '''
        return self._broker
    
    def _brokernotify(self):
        '''
        Internal method which kicks the broker and delivers any broker
        notification to the strategy
        '''
        self._broker.next()
        while True:
            order = self._broker.get_notification()
            if order is None:
                break

            owner = order.owner
            if owner is None:
                owner = self.runningstrats[0]  # default

            owner._addnotification(order, quicknotify=self.p.quicknotify)

    async def on_trade(self, event: TradeEvent):
        """
            Order event push.
        """
        #with ExitStack() as stack:
        #    """
        #    由于已注册的回调是按注册的相反顺序调用的, 因此最终行为就好像with 已将多个嵌套语句与已注册的一组回调一起使用。
        #    这甚至扩展到异常处理-如果内部回调抑制或替换异常，则外部回调将基于该更新状态传递自变量。
        #    enter_context  输入一个新的上下文管理器, 并将其__exit__()方法添加到回调堆栈中。返回值是上下文管理器自己的__enter__()方法的结果。
        #    callback(回调, * args, ** kwds)接受任意的回调函数和参数, 并将其添加到回调堆栈中。
        #    """
        txn = await self.broker.on_trade(event)
        self.position_tracker.update(txn)
        self.avaiable += txn.price * txn.size
        return txn
    
    async def on_event(self, event: Event):
        """
            dividends and rights
        """
        data = await self.position_tracker.process_event(event)
        self.avaiable += data
    
    async def on_sync(self, event: SyncEvent):
        """
            sync close price on positions
            Clear out any assets that have expired and positions which volume is zero before starting a new sim day.
            Finds all assets for which we have positions and generates
            close_position events for any assets that have reached their
            close_date.
        """
        await self.position_tracker.syncronize(event.data)
        positions = self.position_tracker.get_positions()
        portfolio_value, pnl, usage = self.portfolio.calc_portfolio(event.session_ix, positions)
        portfolio_weight = self.portfolio.current_portfolio_weights(positions)
        portfolio_metrics = PortfolioEvent(avaiable=self.avaiable, 
                                           pnl=pnl, 
                                           usage=usage, 
                                           portfolio_value=portfolio_value,
                                           portfolio_weight=portfolio_weight)
        return portfolio_metrics.model_dump_json(indent=4)


ledger = Ledger()
