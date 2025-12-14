import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
import plotly.express as px
from src.rankings import county_rankings

def price_choropleth(df, geo):

    min_year = int(df["Year"].min())
    max_year = int(df["Year"].max())

    year = st.slider(
        "Year",
        min_value=min_year,
        max_value=max_year,
        value=max_year,
        step=1
    )

    quarter = st.radio(
        "Quarter",
        [1, 2, 3, 4],
        horizontal=True
    )

    map_df = df[
        (df["Year"] == year) &
        (df["Quarter"] == quarter)
    ][[
        "County",
        "avg_price",
        "transaction_count"
    ]]

    fig = px.choropleth(
        map_df,
        geojson=geo.__geo_interface__,
        locations="County",
        featureidkey="properties.NAME_1",
        color="avg_price",
        hover_name="County",
        hover_data={
            "avg_price": ":,.0f",
            "transaction_count": True
        },
        color_continuous_scale="rdylgn_r",
        title=f"Average House Prices – {year} Q{quarter}"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, width='stretch')


def growth_choropleth(df, geo):
    st.subheader("House Price Change Map")

    col1, col2, col3, col4 = st.columns([1.2, 2, 3, 2])

    with col1:
        metric = st.radio(
            "Change",
            ["QoQ", "YoY"],
            horizontal=True
        )

    with col2:
        price_type = st.radio(
            "Price",
            ["Nominal", "Real"],
            horizontal=True
        )

    with col3:
        min_year = int(df["Year"].min())
        max_year = int(df["Year"].max())

        year = st.slider(
            "Year",
            min_year,
            max_year,
            max_year
        )

    with col4:
        quarter = st.radio(
            "Quarter",
            [1, 2, 3, 4],
            horizontal=True
        )
        period_label = f"{year} Q{quarter}"


    if metric == "QoQ":
        metric_col = (
        "real_price_qoq_pct"
        if price_type == "Real"
        else "price_qoq_pct"
        )   
        metric_label = "Quarter-on-Quarter"
    else:
        metric_col = (
        "real_price_yoy_pct"
        if price_type == "Real"
        else "price_yoy_pct"
    )
        metric_label = "Year-on-Year"


    # --- Filter data ---
    map_df = (
        df[
            (df["Year"] == year) &
            (df["Quarter"] == quarter)
        ]
        .dropna(subset=[metric_col])
    )

    if map_df.empty:
        st.info("No data available for this period.")
        return

    # --- Rankings synced to map ---
    county_rankings(
        map_df,
        metric_col=metric_col,
        period_label=period_label
    )

    # --- Choropleth ---
    fig = px.choropleth(
        map_df,
        geojson=geo.__geo_interface__,
        locations="County",
        featureidkey="properties.NAME_1",
        color=metric_col,
        hover_name="County",
        hover_data={
            metric_col: ":.2f",
            "avg_price": ":,.0f",
            "transaction_count": True
        },
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        title=f"{metric_label} House Price Change – {period_label} ({price_type})"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, width='stretch')

def range_growth_choropleth(df, geo):

    periods = (
        df[["Year", "Quarter", "Period"]]
        .drop_duplicates()
        .sort_values(["Year", "Quarter"])
        .reset_index(drop=True)
    )

    period_labels = periods["Period"].tolist()

    start_idx, end_idx = st.slider(
        "Select time range",
        min_value=0,
        max_value=len(periods) - 1,
        value=(len(periods) - 8, len(periods) - 2)
    )

    start_period = period_labels[start_idx]
    end_period = period_labels[end_idx]

    start_df = df[df["Period"] == start_period]
    end_df   = df[df["Period"] == end_period]

    merged = (
        start_df[["County", "avg_price"]]
        .merge(
            end_df[["County", "avg_price"]],
            on="County",
            suffixes=("_start", "_end")
        )
    )

    merged["range_change_pct"] = (
        (merged["avg_price_end"] - merged["avg_price_start"])
        / merged["avg_price_start"]
    ) * 100

    county_rankings(
    merged,
    metric_col="range_change_pct",
    period_label=f"{start_period} → {end_period}"
    )

    fig = px.choropleth(
        merged,
        geojson=geo.__geo_interface__,
        locations="County",
        featureidkey="properties.NAME_1",
        color="range_change_pct",
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        hover_name="County",
        hover_data={"range_change_pct": ":.2f"},
        title=f"House Price Change: {start_period} → {end_period}"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, width='stretch')
