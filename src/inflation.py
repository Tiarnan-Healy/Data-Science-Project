def prepare_cumulative_inflation(df):
    df = df.sort_values(["Year", "Quarter"]).copy()

    # Convert YoY % → quarterly growth factor
    df["infl_q_factor"] = (1 + df["Inflation_Rate"] / 100) ** 0.25

    # Build price-level index
    df["Inflation_Index"] = df["infl_q_factor"].cumprod() * 100

    return df
