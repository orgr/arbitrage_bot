import ccxt


def main():
    exchange = ccxt.binance()
    exchange.set_sandbox_mode(enabled=True)
    exchange.load_markets()
    print(exchange.markets.keys())


if __name__ == '__main__':
    main()

