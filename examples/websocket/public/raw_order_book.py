# python -c "import examples.websocket.public.raw_order_book"

from collections import OrderedDict

from typing import List

from bfxapi import Client, PUB_WSS_HOST

from bfxapi.types import TradingPairRawBook
from bfxapi.websocket.subscriptions import Book
from bfxapi.websocket.enums import Channel, Error

class RawOrderBook:
    def __init__(self, symbols: List[str]):
        self.__raw_order_book = {
            symbol: {
                "bids": OrderedDict(), "asks": OrderedDict() 
            } for symbol in symbols
        }

    def update(self, symbol: str, data: TradingPairRawBook) -> None:
        order_id, price, amount = data.order_id, data.price, data.amount

        kind = "bids" if amount > 0 else "asks"

        if price > 0:
            self.__raw_order_book[symbol][kind][order_id] = {
                "order_id": order_id,
                "price": price, 
                "amount": amount 
            }

        if price == 0:
            if order_id in self.__raw_order_book[symbol][kind]:
                del self.__raw_order_book[symbol][kind][order_id]

SYMBOLS = [ "tBTCUSD", "tLTCUSD", "tLTCBTC", "tETHUSD", "tETHBTC" ]

raw_order_book = RawOrderBook(symbols=SYMBOLS)

bfx = Client(wss_host=PUB_WSS_HOST)

@bfx.wss.on("wss-error")
def on_wss_error(code: Error, msg: str):
    print(code, msg)

@bfx.wss.on("open")
async def on_open():
    for symbol in SYMBOLS:
        await bfx.wss.subscribe(Channel.BOOK, symbol=symbol, prec="R0")

@bfx.wss.on("subscribed")
def on_subscribed(subscription):
    print(f"Subscription successful for pair <{subscription['pair']}>")

@bfx.wss.on("t_raw_book_snapshot")
def on_t_raw_book_snapshot(subscription: Book, snapshot: List[TradingPairRawBook]):
    for data in snapshot:
        raw_order_book.update(subscription["symbol"], data)

@bfx.wss.on("t_raw_book_update")
def on_t_raw_book_update(subscription: Book, data: TradingPairRawBook):
    raw_order_book.update(subscription["symbol"], data)

bfx.wss.run()
