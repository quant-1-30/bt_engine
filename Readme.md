simulate 
# 如果价格为接近涨跌幅(threshold=0.1%)则无法成交
# 无法构建orderbook, 只能以溢价模拟成交
# 控制冲击成本 交易量 * thres ( e.g. 70%)
# simulate minute ticker downsample to 3s 
# policy + offset ---> order 
# record order and update ledger by time / by price 

1、tradeapi

    a. on_trade --- direction / symbol 
    b. on_event --- dividend / rights
    c. on_close --- close_position
    d. on_query QueryPosition / onQueryAccount
    e. on_login 

3、 bytes ---> int () int.from_bytes() | struct.unpack(), 大端(human)与小端数据

# python 3.11 asyncio 对udp支持, 之前版本对于tcp stream 
