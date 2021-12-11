import sys
import time
import ccxt


def main():
    if len(sys.argv) < 3:
        print("Usage: python {} <exchange id 1> <exchange id 2> ...".format(sys.argv[0]))
        return
    exchanges = []

    # initialize exchanges
    for ex_id in sys.argv[1:]:
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
        for ex in exchanges:
            orderbook = ex.fetch_order_book(symbol, 10)
            # time.sleep(2)
            bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
            ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
            spread = (ask - bid) if (bid and ask) else None
            print(ex.id, 'market price', {'bid': bid, 'ask': ask, 'spread': spread})

        count += 1
        if count == 2:
            break


if __name__ == '__main__':
    main()

