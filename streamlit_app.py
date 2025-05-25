import streamlit as st
import pandas as pd
import requests

st.title("低市值币种内在价值套利")

# 1. 获取币种市场数据（取前250个币）
@st.cache_data(ttl=3600)
def fetch_market_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_asc",
        "per_page": 250,
        "page": 1,
        "price_change_percentage": "24h"
    }
    resp = requests.get(url, params=params)
    return resp.json()

data = fetch_market_data()

# 2. 构造DataFrame并过滤市值小于3千万
df = pd.DataFrame(data)
df = df[["id", "symbol", "name", "market_cap"]]
df = df[df["market_cap"] < 30_000_000]

# 3. 模拟交易所和类型标签（实际要通过API或手动维护）
# 这里示例随机给一些币赋予属性，你后续可以扩展完善数据源
import random

def random_bool():
    return random.choice([True, False])

df["binance_perp"] = df["id"].apply(lambda x: random_bool())
df["memecoin"] = df["id"].apply(lambda x: random_bool())
df["coinbase_spot"] = df["id"].apply(lambda x: random_bool())
df["upbit_krw_spot"] = df["id"].apply(lambda x: random_bool())

# 4. 根据你的模型计算内在价值
def calc_intrinsic_value(row):
    val = 0
    if row["binance_perp"]:
        val += 10_000_000
    if row["memecoin"]:
        val += 3_000_000
    if row["coinbase_spot"]:
        val += 5_000_000
    if row["upbit_krw_spot"]:
        val += 10_000_000
    return val

df["intrinsic_value"] = df.apply(calc_intrinsic_value, axis=1)
df["undervalue_pct"] = (df["intrinsic_value"] - df["market_cap"]) / df["intrinsic_value"] * 100

# 5. 搜索框和过滤
search = st.text_input("搜索币种（支持名称或符号）").lower()

if search:
    df = df[df["name"].str.lower().str.contains(search) | df["symbol"].str.lower().str.contains(search)]

# 6. 排序并显示
df = df.sort_values(by="undervalue_pct", ascending=False)

st.dataframe(
    df[["name", "symbol", "market_cap", "intrinsic_value", "undervalue_pct", "binance_perp", "memecoin", "coinbase_spot", "upbit_krw_spot"]]
)

st.markdown("""
### 使用说明：
- 数据每小时缓存更新
- 内在价值根据 Binance perp、memecoin、Coinbase spot、Upbit KRW spot 加权计算
- 低估百分比越高，代表价格越有套利潜力
""")
