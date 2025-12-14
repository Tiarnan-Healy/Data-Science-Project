def add_qoq_change(df):
    df = df.sort_values(["County", "Year", "Quarter"]).copy()

    df["qoq_change_pct"] = (
        df
        .groupby("County")["avg_price"]
        .pct_change() * 100
    )

    return df

def add_yoy_change(df):
    df = df.sort_values(["County", "Year", "Quarter"]).copy()

    df["yoy_change_pct"] = (
        df.groupby("County")["avg_price"]
        .pct_change(periods=4) * 100
    )

    return df