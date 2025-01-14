# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload, selectinload
from functools import lru_cache

from core.ops.schema import *
from core.event import LoginEvent
from core.ops.operator import async_ops

router = APIRouter()


def async_lru_cache(func):
    cache = {}
    async def wrapper(*args, **kwargs):
        if (*args, *kwargs) in cache:
            return cache[(*args, *kwargs)]
        else:
            cache[(*args, *kwargs)] = await func(*args, **kwargs)
            return cache[(*args, *kwargs)]
    return wrapper


@async_lru_cache
async def get_current_user(token: str):
    # token to user_id
    req = select(Token).options(joinedload(Token.user)).where(Token.token == token)
    token_obj = await async_ops.on_query_obj(req)
    return token_obj[0].user


@router.post("/on_login")
async def on_login(item: LoginEvent):
    """
        query user info from db and build token to db
    """
    req = select(User).where(and_(User.name == item.name, User.phone == item.phone))
    user = await async_ops.on_query_obj(req)
    if not user:
        assert item.auto_register, "user not found and auto_register is False"
        user_obj = User(name=item.name, phone=item.phone)
        print(user_obj)
        await async_ops.on_insert_obj(user_obj)
        token_obj = Token(user_id=user_obj.id)
        token_obj.user = user_obj
        resp = await async_ops.on_insert_obj(token_obj)
    else:
        req = select(Token).where(Token.user_id == user.id)
        resp = await async_ops.on_query_obj(req)
    return {"token": resp[0].token, "status": "success"}
    #return RedirectResponse(url=f"/register")

@router.get("/on_deploy")
async def on_deploy(token: str):
    user = await get_current_user(token)
    exp_obj = Experiment(user_id=user.id)
    exp_obj.user = user
    resp = await async_ops.on_insert_obj(exp_obj)
    # 返回部署的实验id
    return {"experiment_id": resp[0].experiment_id, "status": "success"}

@router.get("/on_display")
async def on_display(token: str):
    user = await get_current_user(token)
    req = select(Experiment).where(Experiment.user_id == user.id)
    experiment = await async_ops.on_query_obj(req)
    return {"experiment": experiment, "status": "success"}  


@router.get("/api")
def api():
    return {"login": "login"}
