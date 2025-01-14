#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import pdb
import pandas as pd
from core.ops.operator import async_ops

def get_data(req: str):
    df = async_ops.on_query(req)
    return df


if __name__ == "__main__":

    req = "select * from minute where sid = 603676"
    raw = get_data(req)
    pdb.set_trace()
    print(raw)