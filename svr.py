# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import sys
from uuid import uuid4
from pydantic import BaseModel, field_validator
from fastapi import FastAPI, Depends, Request, Response
from core.model import LoginEvent, TradeReq, TradeResp
from core.ledger import ledger


def signal_handler(sig, frame):
    print("\nSignal handler called with signal", sig)
    print("Program will exit now.")
    sys.exit(0)

# register
signal.signal(signal.SIGINT, signal_handler)

app = FastAPI()


async def valid_token(reqeust: Request):
    params = dict(reqeust.query_params)
    if params["token"]:
        return params
    else:
        return {"query": reqeust}
    

# async def get_db():
#         try:
#             yield ""
#         finally:
#             ""

@app.get("/on_connect")
async def login(item: LoginEvent):
    """
        return uuid_token
    """
    token = uuid4()
    return token

@app.get("/on_query/")
async def on_query(valid_query: dict=Depends[valid_token]):
            if not valid_query:
                return Response(content="token is illegal or missing", status_code=301)


@app.post("/on_trade/")
async def on_trade(item: dict = Depends[valid_token]):
            trade_req = TradeReq(item["request"].data)


# checkpoint --- restore --- atexit
# log 
