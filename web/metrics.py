# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter


router = APIRouter()


@router.get("/metrics")
async def metrics():
    return {"metrics": "metrics"}


@router.get("/test")
async def test():
    return {"test": "test"}

