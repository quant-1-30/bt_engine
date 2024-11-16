# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class AsyncOps(object):

    async def get_db(self):
            pass
    
    async def bulk_insert(self, raw):
          pass
    
    async def query(self, query_params):
          pass
    