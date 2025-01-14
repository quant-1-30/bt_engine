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
    phone: Mapped[BigInteger] = mapped_column(BigInteger, unique=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    account_id: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    # 计算默认值用server_default --- dababase 非default --- python
    # 默认日期 func.now / func.current_timestamp()
    register_time: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), use_existing_column=True)

    PrimaryKeyConstraint("user_id", "phone", name="pd_id_phone")

    # backref在主类里面申明 / back_populates显式两个类申明
    # default lazy="select" / "joined" / "selectin" 
    # one to many all, delete-orphan / many to many  all, delete 
    # uselist False -对一
    token: Mapped["Token"] = relationship(
        back_populates="user", cascade="all, delete-orphan")
    
    experiments: Mapped[List["Experiment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    account: Mapped["Account"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, phone={self.phone!r}, user_id={self.user_id!r}, account_id={self.account_id!r}, register_time={self.register_time!r})"


class Token(Base):

    __tablename__ = "token"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, use_existing_column=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_info.id", ondelete="CASCADE"), use_existing_column=True)

    user: Mapped["User"] = relationship(back_populates="token")

    def __repr__(self) -> str:
        return f"Token(id={self.id!r}, token={self.token!r})"


class Experiment(Base):

    # 增加account_id 与 user_id , algo_id映射关系表
    __tablename__ = "experiment"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_info.id", ondelete="CASCADE", onupdate="CASCADE"), use_existing_column=True)
    experiment_id: Mapped[int] = mapped_column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, use_existing_column=True)
    
    PrimaryKeyConstraint("user_id", "id")

    user: Mapped["User"] = relationship(
        back_populates="experiments")
    account: Mapped["Account"] = relationship(
        back_populates="experiments")
    orders: Mapped[List["Order"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan")


#association table 
class Order_Transaction(Base):

    __tablename__ = "order_transaction"
    __table_args__ = {"extend_existing": True}

    # id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("_order.order_id"), primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transaction.transaction_id"), primary_key=True)


class Order(Base):

    __tablename__ = "_order"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sid: Mapped[str] = mapped_column(String(10), nullable=False, use_existing_column=True)
    created_dt: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    order_id: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, unique=True, use_existing_column=True)
    order_type: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    volume: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.id", ondelete="CASCADE"), use_existing_column=True, nullable=False)

    PrimaryKeyConstraint("id", "order_id", name="pk_id_order")
    # PrimaryKeyConstraint("id", name="pk_id")

    experiment: Mapped["Experiment"] = relationship(
        back_populates="orders")

    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="order", secondary="order_transaction", cascade="all, delete"
    )


class Transaction(Base):

    __tablename__ = "transaction"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sid: Mapped[str] = mapped_column(String(10), nullable=False, use_existing_column=True)
    created_dt: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False, unique=True, use_existing_column=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, use_existing_column=True)
    cost: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("_order.order_id", ondelete="CASCADE"), use_existing_column=True)

    PrimaryKeyConstraint("id", "transaction_id", name="pk_id_transaction")
    # PrimaryKeyConstraint("id", name="pk_id")

    order: Mapped["Order"] = relationship(
        back_populates="transactions", secondary="order_transaction", cascade="all, delete")
    

class Account(Base):

    __tablename__ = "account"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[int] = mapped_column(Integer, nullable=False)
    positions: Mapped[str] = mapped_column(Text, nullable=False, use_existing_column=True)
    portfolio: Mapped[int] = mapped_column(BigInteger, nullable=False, use_existing_column=True)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, use_existing_column=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_info.account_id", ondelete="CASCADE"), use_existing_column=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.id", ondelete="CASCADE"), use_existing_column=True)

    user: Mapped["User"] = relationship(
        back_populates="account")
    
    experiments: Mapped[List["Experiment"]] = relationship(
        back_populates="account", cascade="all, delete")

