import streamlit as st import pandas as pd import requests

页面设置

st.set_page_config(page_title="内在价值估值工具", layout="wide") st.title("低市值币种内在价值估算工具")

st.markdown(""" 此工具根据你定义的模型，对币种进行内在价值计算并排序：

Binance perp = $10M

memecoin = $3M

Coinbase 现货 = $5M

Upbit 韩元交易对 = $10M """)


定义估值规则

VALUE_BINANCE_PERP = 10_000_000 VALUE_MEME = 3_000_000 VALUE_COINBASE = 5_000_000 VALUE_UPBIT = 10_000_000

获取 CoinGecko 上的所有币种市值数据（前250个市值最小的）

def get_coin_data(): url = "https://api.coingecko.com/api/v3/coins/markets" params = { 'vs_currency': 'usd', 'order': 'market_cap_asc',  # 按市值升序 'per_page': 250, 'page': 1, 'sparkline': False } response = requests.get(url, params=params) return response.json()

获取是否是 memecoin

MEME_KEYWORDS = ['meme']

def is_memecoin(tags): if not tags: return False for tag in tags: if any(keyword in tag.lower() for keyword in MEME_KEYWORDS): return True return False

判断是否有在各大交易所上线（简化逻辑）

def fetch_exchange_data(coin_id): url = f"https://api.coingecko.com/api/v3/coins/{coin_id}" resp = requests.get(url) if resp.status_code != 200: return None data = resp.json() tickers = data.get("tickers", [])

has_binance_perp = any(
    t.get("market", {}).get("name") == "Binance" and "perp" in t.get("symbol", "").lower()
    for t in tickers)
has_coinbase = any("Coinbase" in t.get("market", {}).get("name", "") for t in tickers)
has_upbit_krw = any("Upbit" in t.get("market", {}).get("name", "") and 
                    t.get("target", "").upper() == "KRW"
                    for t in tickers)

return has_binance_perp, has_coinbase, has_upbit_krw

主函数

with st.spinner("正在抓取实时币种数据..."): coins = get_coin_data() result = []

for coin in coins:
    if coin['market_cap'] is None or coin['market_cap'] > 30_000_000:
        continue  # 只分析低市值币种

    coin_id = coin['id']
    name = coin['name']
    symbol = coin['symbol'].upper()
    market_cap = coin['market_cap']

    extra = fetch_exchange_data(coin_id)
    if extra is None:
        continue

    has_binance_perp, has_coinbase, has_upbit_krw = extra

    # 获取是否为meme币（根据tags）
    tags = coin.get("categories") or coin.get("tags") or []
    meme_flag = is_memecoin(tags)

    intrinsic = 0
    if has_binance_perp:
        intrinsic += VALUE_BINANCE_PERP
    if meme_flag:
        intrinsic += VALUE_MEME
    if has_coinbase:
        intrinsic += VALUE_COINBASE
    if has_upbit_krw:
        intrinsic += VALUE_UPBIT

    under_value = intrinsic - market_cap

    result.append({
        "币种": name,
        "代码": symbol,
        "现市值 ($)": market_cap,
        "估算内在价值 ($)": intrinsic,
        "低估程度 ($)": under_value,
        "Binance perp": "有" if has_binance_perp else "无",
        "Coinbase": "有" if has_coinbase else "无",
        "Upbit KRW": "有" if has_upbit_krw else "无",
        "是Memecoin": "是" if meme_flag else "否",
    })

df = pd.DataFrame(result)
df = df.sort_values(by="低估程度 ($)", ascending=False)

st.success(f"共分析 {len(df)} 个低市值币种")
st.dataframe(df, use_container_width=True)

st.caption("数据来源：CoinGecko API，仅供学习交流")

