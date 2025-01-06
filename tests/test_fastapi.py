#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest



class TestFastApi:

    @pytest.fixture
    def patch(self):
        return 

    def test_login(self):
        return {"login": "login"}
    
    def test_deploy(self):
        return {"deploy": "deploy"}
    
    def test_logout(self):
        return {"logout": "logout"}
    
    # def test_on_trade(self):
    #     return {"on_trade": "on_trade"}
    
    # def test_on_event(self):
    #     return {"on_event": "on_event"}

    # def test_on_sync(self):
    #     return {"on_sync": "on_sync"}
    
    # def test_on_metrics(self):
    #     return {"on_portfolio": "on_portfolio"}
    
