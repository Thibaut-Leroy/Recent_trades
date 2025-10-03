import asyncio
import json
import os
from datetime import datetime
import pytz
from websockets import connect
from termcolor import cprint

#list of symbol i want to track
symbols = ['BTC', 'ETH', 'SOL','HYPE']
websockets_url_base = 'wss://api.hyperliquid.xyz/ws'
trades_filename = 'hyperliquid_trade.csv'

# check if the csv files exist
if not os.path.isfile(trades_filename):
    with open(trades_filename, 'w') as f:
        f.write('Event Time, Symbol, Aggregate Trade ID, Price, Quantity, First Trade ID, Trade Time, Is Buyer Maker\n')

async def hyperliquid_trade_stream(uri, symbol, filename):
    async with connect(uri) as websocket:
        sub_msg = {
            "method": "subscribe",
            "subscription": {
                "type": "trades",
                "coin": symbol
            }
        }
        await websocket.send(json.dumps(sub_msg))

        while True:
            try:
                message =  await websocket.recv()
                data = json.loads(message)

                if data["channel"] != 'trades':
                    continue
                
                for trade in data['data']:
                    symbol = trade["coin"]
                    side = str(trade["side"])
                    price = float(trade["px"])
                    size = float(trade["sz"])
                    trade_time = int(trade["time"])
                    trade_id = trade["tid"]
                    usd_size = price * size
                    est = pytz.timezone("Europe/Paris")
                    readable_trade_time = datetime.fromtimestamp(trade_time/1000, est).strftime("%H:%M:%S")

                if usd_size > 499:
                    trade_type = 'SELL' if side == "B" else 'BUY'
                    color = 'red' if trade_type == 'SELL' else 'green'

                    stars = ''
                    attrs = ['bold'] if usd_size > 50000 else []
                    repeat_count = 1

                    if usd_size > 50000:
                        stars = '*' * 2
                        repeat_count = 1
                        if trade_type == 'SELL':
                            color = 'magenta'
                        else:
                            color = 'blue'
                    elif usd_size > 10000:
                        stars = '*' * 1
                        repeat_count = 1

                    output = f"{stars} {trade_type} {symbol} {readable_trade_time} ${usd_size:,.0f} "
                    for _ in range(repeat_count):
                        cprint(output, 'white',f'on_{color}', attrs=attrs)

                    # lof csv file
                    with open(filename,'a') as f:
                        f.write(f"{trade_time}, {symbol}, {trade_id}, {price},{size},"
                                f"{trade_time},{side}\n")
            
            except Exception as e:
                await asyncio.sleep(1)
     

async def main():
    filename = 'hyperliquid_trade.csv'

    # create a task for each symbol
    tasks = []
    for symbol in symbols:
        stream_url = websockets_url_base
        tasks.append(hyperliquid_trade_stream(stream_url, symbol, filename))
    
    await asyncio.gather(*tasks)

asyncio.run(main())
