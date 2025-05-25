import streamlit as st
import requests
import pandas as pd
from time import sleep

st.set_page_config(page_title="小市值币种套利工具", layout="wide")

# 获取市场币种列表（CoinGecko）
@st.cache_data(ttl=600)
def fetch_market_data(per_page=50, page=1):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_asc",
        "per_page": per_page,
        "page": page,
        "sparkline": False
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

# 获取某币交易所行情（tickers）
@st.cache_data(ttl=600)
def fetch_tickers(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/tickers"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("tickers", [])

# 计算内在价值
def calc_intrinsic_value(coin, tickers):
    value = 0
    memecoins_keywords = ['doge', 'shiba', 'bonk', 'pepe', 'cat', 'elon']
    name = coin['name'].lower()

    has_binance_perp = any(
        ticker['market'] and 'binance' in ticker['market']['name'].lower() and
        'perpetual' in (ticker.get('contract_type') or '').lower()
        for ticker in tickers
    )
    has_coinbase_spot = any(
        ticker['market'] and 'coinbase' in ticker['market']['name'].lower()
        for ticker in tickers
    )
    has_upbit_krw = any(
        ticker['market'] and 'upbit' in ticker['market']['name'].lower() and
        'krw' in ticker['target'].lower()
        for ticker in tickers
    )

    if has_binance_perp:
        value += 10_000_000
    if any(k in name for k in memecoins_keywords):
        value += 3_000_000
    if has_coinbase_spot:
        value += 5_000_000
    if has_upbit_krw:
        value += 10_000_000

    return value

# 新增实时币种数据抓取
@st.cache_data(ttl=300)
def fetch_realtime_coins(vs_currency="usd", per_page=50, page=1):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "sparkline": False,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def show_realtime_data():
    st.header("实时币种市场数据")
    coins = fetch_realtime_coins(per_page=50)
    df = pd.DataFrame(coins)[["name", "symbol", "current_price", "market_cap", "total_volume", "price_change_percentage_24h"]]
    df.rename(columns={
        "name": "名称",
        "symbol": "代码",
        "current_price": "当前价格 (USD)",
        "market_cap": "市值 (USD)",
        "total_volume": "24小时交易量",
        "price_change_percentage_24h": "24小时涨跌幅 (%)"
    }, inplace=True)
    st.dataframe(df)

def main():
    st.title("小市值币种套利工具")

    st.info("正在抓取币种数据，可能需要几秒钟，请稍等...")

    # 主功能：展示内在价值计算及折价情况
    market_data = fetch_market_data()

    data = []
    for coin in market_data:
        tickers = fetch_tickers(coin['id'])
        intrinsic_value = calc_intrinsic_value(coin, tickers)
        fdv = coin.get('fully_diluted_valuation') or 0
        discount = (intrinsic_value - fdv) / intrinsic_value if intrinsic_value > 0 else 0

        data.append({
            "名称": coin['name'],
            "代码": coin['symbol'].upper(),
            "FDV (USD)": fdv,
            "内在价值 (USD)": intrinsic_value,
            "折价率 %": round(discount * 100, 2),
            "Binance perp": "是" if any(
                ticker['market'] and 'binance' in ticker['market']['name'].lower() and
                'perpetual' in (ticker.get('contract_type') or '').lower()
                for ticker in tickers
            ) else "否",
            "Coinbase spot": "是" if any(
                ticker['market'] and 'coinbase' in ticker['market']['name'].lower()
                for ticker in tickers
            ) else "否",
            "Upbit KRW": "是" if any(
                ticker['market'] and 'upbit' in ticker['market']['name'].lower() and
                'krw' in ticker['target'].lower()
                for ticker in tickers
            ) else "否",
            "是否Memecoin": "是" if any(k in coin['name'].lower() for k in ['doge', 'shiba', 'bonk', 'pepe', 'cat', 'elon']) else "否"
        })

        sleep(0.5)  # 降低请求频率，避免被限流

    df = pd.DataFrame(data).sort_values(by="折价率 %", ascending=False)

    def highlight_discount(row):
        return ['background-color: #ffcccc' if row["折价率 %"] > 30 else '' for _ in row]

    st.subheader("币种内在价值折价情况")
    st.dataframe(df.style.apply(highlight_discount, axis=1), height=700)

    # 新增：展示实时币种数据表
    show_realtime_data()

if __name__ == "__main__":
    main()