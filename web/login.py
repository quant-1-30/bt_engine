# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from uuid import uuid4
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from core.event import LoginEvent

router = APIRouter()


def get_current_user():
    # 假设是一个获取当前用户的依赖
    return {"username": "johndoe"}

@router.get("/test/", dependencies=[Depends(get_current_user)])
async def read_profile():
    return {"profile": "User profile data"}


@router.post("/on_connect")
async def login(item: LoginEvent):
    """
        first login / insert user / address data to db
    """
    return RedirectResponse(url=f"/register")


@router.get("/register")
async def register():
    return {"register": "register"}

@router.get("/deploy")
async def deploy():
    # deploy experiment and insert to db
    return {"deploy": "deploy"}


