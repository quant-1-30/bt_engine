#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from core.ops.operator import async_ops


if __name__ == "__main__":

    # user table
    user_data = [{"name": "hx", "phone": 1234567890}]
    asyncio.run(async_ops.on_insert("user_info", user_data))

    # # address table
    # address_data = [{"user_id": "c7963e3d-d87e-4ebb-95d0-22ebae75ebff", "email": "1234567890"}]
    # asyncio.run(async_ops.on_insert("address", address_data))

    # # experiment table
    # experiment_data = [{"account_id": "981baa7f-e4a2-4444-84bc-2ae9ff60c26c", "experiment_id": "1234567890"}]
    # asyncio.run(async_ops.on_insert("experiment", experiment_data))

    # # order table
    # order_data = [{"sid": "000001", "created_dt": "1234567890", "order_id": "1234567890", 
    #                "order_type": 1, "price": 100, "volume": 100}]
    # asyncio.run(async_ops.on_insert("order", order_data))

    # transaction table
    # transaction_data = [{"sid": "000001", "created_dt": "1234567890", 
    #                      "transaction_id": "1234567890", 
    #                      "price": 100, "volume": 100, "cost": 100}]
    # asyncio.run(async_ops.on_insert("transaction", transaction_data))

    # # account table
    # account_data = [{"date": 20250101, "positions": "1234567890", 
    #                    "portfolio": 100, "balance": 100}]
    # asyncio.run(async_ops.on_insert("account", account_data))
