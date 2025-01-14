
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
import pandas as pd
from toolz import valmap


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

    def __repr__(self):
        return f"Portfolio(initial_balance={self.initial_balance}, \
        portfolio_daily_value={self.portfolio_daily_value}, \
        pnl={self.pnl})"