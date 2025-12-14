import pandas as pd

def prepare_price_index(df):
    df = df.sort_values(["Year", "Quarter"]).copy()
    base_price = df.iloc[0]["avg_price"]
    df["Price_Index"] = (df["avg_price"] / base_price) * 100
    return df