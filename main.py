import sys
import time
from typing import List

import ccxt
import itertools

import enum


class ArbitrageOpportunity(enum.Enum):
    NONE = 0
    BUY = 1
    SELL = 2


class Price:
    delta_threshold = 0

    def __init__(self, exchange, symbol, bid, ask):
        self.exchange = exchange
        self.symbol = symbol
        self.bid = bid
        self.ask = ask

    def is_opportunity(self, other):
        if self.bid + Price.delta_threshold > other.ask:
            return ArbitrageOpportunity.BUY  # buy from other exchange
        if self.ask + Price.delta_threshold < other.bid:
            return ArbitrageOpportunity.SELL  # buy from this exchange

        return ArbitrageOpportunity.NONE


def main():
    if len(sys.argv) < 3:
        print("Usage: python {} <delta threshold> <exchange id 1> <exchange id 2> ...".format(sys.argv[0]))
        return
    exchanges = []
    Price.delta_threshold = int(sys.argv[1])

    # initialize exchanges
    for ex_id in sys.argv[2:]:
        try:
            ex = getattr(ccxt, ex_id)({'enableRateLimit': True})  # type: ccxt.Exchange
            ex.load_markets()
            # ex.set_sandbox_mode(enabled=True)
        except AttributeError:
            print("{} is not supported".format(ex_id))
            return
        except ccxt.NotSupported:
            print("{} paper trading is not supported".format(ex_id))
            return
        exchanges.append(ex)

    all_symbols = [symbol for ex in exchanges for symbol in ex.symbols]
    unique_arbitrable_symbols = set([symbol for symbol in all_symbols if all_symbols.count(symbol) > 1])

    count = 0
    for symbol in unique_arbitrable_symbols:
        print(symbol)
        prices: List[Price] = []
        for ex in exchanges:
            orderbook = ex.fetch_order_book(symbol, 10)
            # time.sleep(2)
            bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
            ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
            spread = (ask - bid) if (bid and ask) else None
            print(ex.id, 'market price', {'bid': bid, 'ask': ask, 'spread': spread})
            prices.append(Price(ex, symbol, float(bid), float(ask)))

        arbitrage_pairs = itertools.combinations(prices, r=2)
        for p in arbitrage_pairs:
            print(p[0].is_opportunity(p[1]))
        count += 1
        if count == 2:
            break


if __name__ == '__main__':
    main()

