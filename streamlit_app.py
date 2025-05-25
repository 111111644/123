import streamlit as st
import pandas as pd
import requests
import random

st.title("低市值币种内在价值套利")

@st.cache_data(ttl=3600)
def fetch_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_asc",
        "per_page": 250,
        "page": 1,
        "price_change_percentage": "24h"
    }
    r = requests.get(url, params=params)
    return r.json()

data = fetch_data()
df = pd.DataFrame(data)
df = df[["id", "symbol", "name", "market_cap"]]
df = df[df["market_cap"] < 30_000_000]

def rand(): return random.choice([True, False])
df["binance_perp"] = df["id"].apply(lambda x: rand())
df["memecoin"] = df["id"].apply(lambda x: rand())
df["coinbase_spot"] = df["id"].apply(lambda x: rand())
df["upbit_krw_spot"] = df["id"].apply(lambda x: rand())

def calc_val(row):
    val = 0
    if row["binance_perp"]: val += 10_000_000
    if row["memecoin"]: val += 3_000_000
    if row["coinbase_spot"]: val += 5_000_000
    if row["upbit_krw_spot"]: val += 10_000_000
    return val

df["intrinsic_value"] = df.apply(calc_val, axis=1)
df["undervalue_pct"] = (df["intrinsic_value"] - df["market_cap"]) / df["intrinsic_value"] * 100

s = st.text_input("搜索币名/代号").lower()
if s:
    df = df[df["name"].str.lower().str.contains(s) | df["symbol"].str.lower().str.contains(s)]

df = df.sort_values(by="undervalue_pct", ascending=False)
st.dataframe(df[["name", "symbol", "market_cap", "intrinsic_value", "undervalue_pct"]])