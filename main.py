import sys
import time
from typing import List

import asyncio
import ccxt.async_support as ccxt
# import ccxt
import itertools

from enum import Enum


class Color(Enum):
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'


def colorize(s, color: Color):
    # return color.value + s + Color.RESET.value
    return "{}{}{}".format(color.value, s, Color.RESET.value)


def green(s):
    return colorize(s, Color.GREEN)


def yellow(s):
    return colorize(s, Color.YELLOW)


def red(s):
    return colorize(s, Color.RED)


class ArbitrageOpportunity(Enum):
    NONE = 0
    BUY = 1
    SELL = 2

    def __str__(self):
        return self.name


def get_complementary_trade(t: ArbitrageOpportunity):
    assert (t != ArbitrageOpportunity.NONE)
    return ArbitrageOpportunity.BUY if t == ArbitrageOpportunity.SELL else ArbitrageOpportunity.SELL


class Price:

    def __init__(self, exchange, symbol, bid, ask):
        self.exchange = exchange
        self.symbol = symbol
        self.bid = bid
        self.ask = ask

    def is_opportunity(self, other):
        if self.bid > other.ask:
            return ArbitrageOpportunity.BUY  # buy from other exchange
        if self.ask < other.bid:
            return ArbitrageOpportunity.SELL  # buy from this exchange

        return ArbitrageOpportunity.NONE


def compare_prices(p1: Price, p2: Price):
    return p1.is_opportunity(p2)


async def get_price(symbol, exchange) -> Price:
    orderbook = await exchange.fetch_order_book(symbol, 10)
    bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
    ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
    # spread = (ask - bid) if (bid and ask) else None
    # print(ex.id, 'market price', {'bid': bid, 'ask': ask, 'spread': spread})
    if bid is None or ask is None:
        return None

    return Price(exchange, symbol, float(bid), float(ask))


async def main():
    if len(sys.argv) < 3:
        print("Usage: python {} <exchange id 1> <exchange id 2> ...".format(sys.argv[0]))
        return
    exchanges = []

    try:
        # initialize exchanges
        tasks = []
        for ex_id in sys.argv[1:]:
            try:
                ex = getattr(ccxt, ex_id)({'enableRateLimit': True})  # type: ccxt.Exchange
                # ex.set_sandbox_mode(enabled=True)
            except AttributeError:
                print("{} is not supported".format(ex_id))
                return
            except ccxt.NotSupported:
                print("{} paper trading is not supported".format(ex_id))
                return

            tasks.append(asyncio.create_task(ex.load_markets()))
            exchanges.append(ex)

        [await t for t in tasks]

        all_symbols = [symbol for ex in exchanges for symbol in ex.symbols]
        unique_arbitrable_symbols = set([symbol for symbol in all_symbols if all_symbols.count(symbol) > 1])

        for symbol in unique_arbitrable_symbols:
            tasks = []
            for ex in exchanges:
                tasks.append(asyncio.create_task(get_price(symbol, ex)))

            [await t for t in tasks]
            prices = [t.result() for t in tasks]

            if len(prices) > 1:
                arbitrage_pairs = itertools.combinations(prices, r=2)
                for p in arbitrage_pairs:
                    opportunity = compare_prices(p[0], p[1])
                    if opportunity != ArbitrageOpportunity.NONE:
                        print(green("{}: {} from {}, {} from {}".format(symbol, opportunity, p[1].exchange.id,
                                                                        get_complementary_trade(opportunity),
                                                                        p[0].exchange.id)))
                    else:
                        print(yellow(symbol))

    # close all connections on KeyboardInterrupts and errors
    finally:
        [await ex.close() for ex in exchanges]


if __name__ == '__main__':
    asyncio.run(main())
