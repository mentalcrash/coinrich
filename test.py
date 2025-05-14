from coinrich.service.upbit_api import UpbitAPI

if __name__ == "__main__":
    api = UpbitAPI()
    
    # 마켓 조회
    print("=== 마켓 조회 ===")
    markets = api.get_markets(is_details=True)
    print(f"마켓 수: {len(markets)}")
    print(f"첫 번째 마켓: {markets[0].market}, {markets[0].korean_name}")
    print()
    
    # 현재가 조회 - 단일 종목
    print("=== 단일 종목 현재가 조회 ===")
    btc_ticker = api.get_ticker("KRW-BTC")
    print(f"비트코인 현재가: {btc_ticker.trade_price:,}원")
    print(f"전일 대비: {btc_ticker.signed_change_rate * 100:.2f}% ({btc_ticker.change})")
    print(f"거래량(24h): {btc_ticker.acc_trade_volume_24h:.4f} BTC")
    print(f"거래대금(24h): {btc_ticker.acc_trade_price_24h / 1000000:.2f}백만원")
    print()
    
    # 현재가 조회 - 여러 종목
    print("=== 여러 종목 현재가 조회 ===")
    top_coins = api.get_ticker(["KRW-BTC", "KRW-ETH", "KRW-XRP"])
    
    for ticker in top_coins:
        sign = "+" if ticker.signed_change_rate > 0 else ""
        print(f"{ticker.market}: {ticker.trade_price:,}원 ({sign}{ticker.signed_change_rate * 100:.2f}%)")
