#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pdb
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from .schema import Base


def builder(cls):
    """
        a. create all tables
        b. reflect tables
        c. bug --- every restart service result scan model to recreate (rollback)
    """
    # postgresql+psycopg2cffi://user:password@host:port/dbname[?key=value&key=value...]
    # postgresql+psycopg2://me@localhost/mydb
    # postgresql+asyncpg://me@localhost/mydb
    print("builder ", cls)
    url = f"postgresql+{cls.p.engine}://{cls.p.user}:{cls.p.pwd}@{cls.p.host}:{cls.p.port}/{cls.p.db}"
    # pdb.set_trace()
    # isolation_level="AUTOCOMMIT"
    # engine = create_engine(url, 
    engine = create_async_engine(url, 
                           pool_size=cls.p.pool_size, 
                           max_overflow=cls.p.max_overflow,
                           # 每小时回收连接
                           pool_recycle=3600, 
                           # 使用 ping 检查连接有效性 
                           pool_pre_ping=cls.p.pool_pre_ping,
                           echo=cls.p.echo)
    Base.metadata.create_all(engine)
    Base.metadata.reflect(bind=engine)
    reflections = Base.metadata.tables

    setattr(cls, "engine", engine)
    setattr(cls, "tables", reflections)
    return cls