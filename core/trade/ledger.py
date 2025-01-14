
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
from typing import List, Tuple
from core.trade.position import PositionTracker
from core.broker.broker import BtBroker
from core.event import EquityEvent, TradeEvent, SyncEvent
from core.const import DEFAULT_CAPITAL_BASE
from core.trade.portfolio import Portfolio
from core.trade.order import create_order
from .meta import AccountMeta, MetricsMeta


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
        order = create_order(event.orderMeta)
        txn = await self.broker.on_trade(order, event.payload)
        self.position_tracker.update(txn)
        self.avaiable += txn.price * txn.size
        return order, txn
    
    async def on_event(self, event: EquityEvent):
        """
            dividends and rights
        """
        data = await self.position_tracker.process_event(event)
        self.avaiable += data
    
    async def on_end_of_day(self, event: SyncEvent)-> Tuple[AccountMeta, MetricsMeta]:
        """
            sync close price on positions
            Clear out any assets that have expired and positions which volume is zero before starting a new sim day.
            Finds all assets for which we have positions and generates
            close_position events for any assets that have reached their
            close_date.
        """
        await self.position_tracker.syncronize(event.meta, event.session_ix) 
        positions = self.position_tracker.get_positions()
        portfolio_value, pnl, usage = self.portfolio.calc_portfolio(event.session_ix, positions)
        account = AccountMeta(date=event.session_ix, positions=positions, portfolio = portfolio_value, balance=self.avaiable)  
        # metrics
        portfolio_weight = self.portfolio.current_portfolio_weights(positions)
        metrics = MetricsMeta(pnl=pnl, usage=usage, portfolio_weight=portfolio_weight)
        return (account, metrics)
    

ledger = Ledger()
