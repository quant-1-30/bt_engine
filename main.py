# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from web import app
import uvicorn


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
