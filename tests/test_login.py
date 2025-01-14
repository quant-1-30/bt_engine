#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import httpx
from urllib.parse import urljoin


class TestLoginRouter:

    @pytest.fixture
    def patch(self):
        return urljoin("http://localhost:8100", "/user/")
    
    @pytest.fixture
    def patch_login(self):
        params = {"name": "test", "phone": 1234567890, "email": "test@test.com", "auto_register": True}
        return params
    
    @pytest.fixture
    def patch_token(self):
        params = {"token": "70d4c731-484a-402e-9d64-2b83ba6558cc"}
        return params

    # def test_api(self, patch):
    #     url = urljoin(patch, "api")
    #     response = httpx.get(url)
    #     assert response.status_code == 200

    # def test_login(self, patch, patch_login):
    #     url = urljoin(patch, "on_login")
    #     response = httpx.post(url, json=patch_login)
    #     assert response.status_code == 200
    #     print(response.json())
    #     assert response.json()["status"] == "success"

    # def test_deploy(self, patch, patch_token):
    #     url = urljoin(patch, "on_deploy")
    #     response = httpx.get(url, params=patch_token)
    #     print(response.json())
    #     assert response.status_code == 200
    #     assert response.json()["status"] == "success"

    def test_display(self, patch, patch_token):
        url = urljoin(patch, "on_display")
        response = httpx.get(url, params=patch_token)
        print(response.json())
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    
    