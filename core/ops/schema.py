#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import uuid
from typing import List
from typing import Optional
from sqlalchemy import func
from sqlalchemy import Integer, String, ForeignKey, BigInteger, Text, UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.schema import PrimaryKeyConstraint


# declarative base class
class Base(DeclarativeBase):
    pass


class User(Base):

    __tablename__ = "user_info"
    __table_args__ = {"extend_existing": True}
    # __table_args__ = (PrimaryKeyConstraint("id", "***"),)

    # primary = unique + not null
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), use_existing_column=True)
    phone: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    account_id: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    # 计算默认值用server_default --- dababase 非default --- python
    # 默认日期 func.now / func.current_timestamp()
    register_time: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), use_existing_column=True)

    PrimaryKeyConstraint("user_id", "phone", name="pd_id_phone")

    # backref在主类里面申明 / back_populates显式两个类申明
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    experiment: Mapped[List["Experiment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}), name={self.name!r}, fullname={self.fullname!r}"
    

class Address(Base):

    __tablename__ = "address"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_info.user_id", ondelete="CASCADE"), use_existing_column=True)

    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"


class Experiment(Base):

    # 增加account_id 与 user_id , algo_id映射关系表
    __tablename__ = "experiment"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_info.account_id", ondelete="CASCADE", onupdate="CASCADE"), use_existing_column=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(String(20), nullable=False, use_existing_column=True)

    PrimaryKeyConstraint("user_id", "")

    user: Mapped["User"] = relationship(back_populates="experiment")
    order: Mapped[List["Order"]] = relationship(back_populates="experiment")
    transaction: Mapped[List["Transaction"]] = relationship(back_populates="experiment")
    portfolio: Mapped[List["Portfolio"]] = relationship(back_populates="experiment")
 

class Order(Base):

    __tablename__ = "order"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sid: Mapped[str] = mapped_column(String(10), nullable=False, use_existing_column=True)
    created_dt: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    order_id: Mapped[int] = mapped_column(String(64), primary_key=True, nullable=False, unique=True, use_existing_column=True)
    order_type: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    volume: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)

    PrimaryKeyConstraint("sid", "order_id", name="pk_sid_order")

    experiment: Mapped["Experiment"] = relationship(
        back_populates="order", cascade="all, delete-orphan")

    transactions: Mapped[List["Transaction"]] = relationship(
        # uselist False -对一
        back_populates="order", cascade="all, delete-orphan"
    )


class Transaction(Base):

    __tablename__ = "transaction"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sid: Mapped[str] = mapped_column(String(10), nullable=False, use_existing_column=True)
    created_at: Mapped[int] = mapped_column(Integer, primary_key=True,nullable=False, use_existing_column=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, use_existing_column=True)
    cost: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)

    PrimaryKeyConstraint("id", "sid", name="pk_id_sid")

    experiment: Mapped["Experiment"] = relationship(
        back_populates="transaction", cascade="all, delete-orphan")
    order: Mapped["Order"] = relationship(
        back_populates="transactions", cascade="all, delete-orphan")


class Portfolio(Base):

    __tablename__ = "portfolio"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True, nullable=False)
    positions: Mapped[str] = mapped_column(Text, nullable=False, use_existing_column=True)
    portfolio: Mapped[int] = mapped_column(BigInteger, nullable=False, use_existing_column=True)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)

    experiment: Mapped["Experiment"] = relationship(
        back_populates="account", cascade="all, delete-orphan")
