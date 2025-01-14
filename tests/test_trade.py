#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import pytest
import httpx
from urllib.parse import urljoin


class TestTradeRouter:

    @pytest.fixture
    def patch(self):
        return urljoin("http://localhost:8100", "/trade/")
    
    @pytest.fixture
    def patch_execute(self):
        asset = {"sid": "600001", "first_trading": 100000, "delist": 0}
        orderMeta = {"asset": asset, "order_type": 4, 
                     "direction": 1, "amount": 100000, 
                     "price": 100}
        token = "70d4c731-484a-402e-9d64-2b83ba6558cc"
        experiment_id = "b6e33fc9-8b78-4e0c-b061-31777aa9c8de"
        payload = pd.read_csv("data/test.csv")
        return {"orderMeta": orderMeta, "payload": payload, "token": token, "experiment_id": experiment_id}
    
    @pytest.fixture
    def patch_event(self):
        params = {"token": "70d4c731-484a-402e-9d64-2b83ba6558cc"}
        return params
    
    @pytest.fixture
    def patch_sync(self):
        params = {"token": "70d4c731-484a-402e-9d64-2b83ba6558cc"}
        return params
    
    def test_execute(self, patch, patch_execute):
        url = urljoin(patch, "on_execute")
        response = httpx.post(url, json=patch_execute)
        assert response.status_code == 200

    def test_event(self, patch, patch_event):
        url = urljoin(patch, "on_event")
        response = httpx.post(url, json=patch_event)
        assert response.status_code == 200
        print(response.json())
        assert response.json()["status"] == "success"

    def test_sync(self, patch, patch_sync):
        url = urljoin(patch, "on_sync")
        response = httpx.post(url, params=patch_sync)
        print(response.json())
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_api(self, patch):
        url = urljoin(patch, "api")
        response = httpx.get(url)
        print(response.json())
        assert response.status_code == 200
    
    
    