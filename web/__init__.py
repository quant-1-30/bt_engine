# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import sys
import atexit
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .login import router as login_router
from .trade import router as trade_router
from .metrics import router as metrics_router

# 创建 FastAPI 应用
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源。可以是特定域名列表。
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法（如 GET、POST）。
    allow_headers=["*"],  # 允许所有头。
)
    

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 在请求到达路由之前运行的代码
    print(f"Incoming request: {request.method} {request.url}")
    
    response = await call_next(request)  # 调用下一个中间件或路由处理函数

    # 在响应返回之前运行的代码
    print(f"Outgoing response status: {response.status_code}")
    return response


# 将 APIRouter 实例包含到主应用程序中
app.include_router(login_router, prefix="/login")
app.include_router(trade_router, prefix="/trade")
app.include_router(metrics_router, prefix="/metrics")