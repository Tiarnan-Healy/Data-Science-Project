import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from src.ui import period_range_selector
from src.inflation import prepare_cumulative_inflation

ROI_COUNTIES = {
    "Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry","Kildare",
    "Kilkenny","Laois","Leitrim","Limerick","Longford","Louth","Mayo","Meath",
    "Monaghan","Offaly","Roscommon","Sligo","Tipperary","Waterford","Westmeath",
    "Wexford","Wicklow"
}

def _weighted_price(g):
    w = g["transaction_count"].fillna(0)
    x = g["avg_price"].fillna(0)
    return (x * w).sum() / w.sum() if w.sum() else None


def price_vs_inflation(df: pd.DataFrame):
    st.subheader("House Prices vs Inflation (Indexed Comparison)")

    # ---- Sort & split NI / RoI ----
    df = df.sort_values(["Year", "Quarter"]).copy()

    is_roi = df["County"].str.title().isin(ROI_COUNTIES)
    roi_df = df[is_roi]
    ni_df  = df[~is_roi]

    # ---- Aggregate to national quarterly series ----
    roi_q = (
        roi_df.groupby(["Year", "Quarter", "Period"], as_index=False)
        .apply(lambda g: pd.Series({
            "price": _weighted_price(g),
            "infl_yoy": g["Inflation_Rate"].mean()
        }))
    )

    ni_q = (
        ni_df.groupby(["Year", "Quarter", "Period"], as_index=False)
        .apply(lambda g: pd.Series({
            "price": _weighted_price(g),
            "infl_yoy": g["Inflation_Rate"].mean()
        }))
    )

    # ---- Choose base period for HOUSE PRICES only ----
    common_periods = sorted(set(roi_q["Period"]) & set(ni_q["Period"]))

    if not common_periods:
        st.warning("No overlapping periods between NI and RoI.")
        return

    base_period = st.selectbox(
        "Base quarter for house price index (100)",
        common_periods,
        index=0
    )

    roi_base = roi_q.loc[roi_q["Period"] == base_period].iloc[0]
    ni_base  = ni_q.loc[ni_q["Period"] == base_period].iloc[0]

    # ---- Index house prices ----
    roi_q["price_idx"] = (roi_q["price"] / roi_base["price"]) * 100
    ni_q["price_idx"]  = (ni_q["price"]  / ni_base["price"])  * 100

    # ---- Inflation display: YoY centred on 100 (100 = 0%) ----
    roi_q["infl_display"] = 100 + roi_q["infl_yoy"]
    ni_q["infl_display"]  = 100 + ni_q["infl_yoy"]

    # ---- Line toggles ----
    col1, col2 = st.columns(2)

    with col1:
        show_roi_prices = st.checkbox("RoI House Prices", True)
        show_ni_prices  = st.checkbox("NI House Prices", True)

    with col2:
        show_roi_infl = st.checkbox("RoI Inflation (YoY)", False)
        show_ni_infl  = st.checkbox("NI Inflation (YoY)", False)

    # ---- Build chart (single axis) ----
    fig = go.Figure()

    if show_roi_prices:
        fig.add_trace(go.Scatter(
            x=roi_q["Period"],
            y=roi_q["price_idx"],
            name="RoI House Prices",
            mode="lines"
        ))

    if show_ni_prices:
        fig.add_trace(go.Scatter(
            x=ni_q["Period"],
            y=ni_q["price_idx"],
            name="NI House Prices",
            mode="lines"
        ))

    if show_roi_infl:
        fig.add_trace(go.Scatter(
            x=roi_q["Period"],
            y=roi_q["infl_display"],
            name="RoI Inflation (YoY)",
            mode="lines",
            line=dict(dash="dot")
        ))

    if show_ni_infl:
        fig.add_trace(go.Scatter(
            x=ni_q["Period"],
            y=ni_q["infl_display"],
            name="NI Inflation (YoY)",
            mode="lines",
            line=dict(dash="dot")
        ))

    # ---- Reference line ----
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="gray",
        annotation_text="Inflation = 0%",
        annotation_position="bottom right"
    )

    # ---- Layout ----
    fig.update_layout(
        title="House Prices vs Inflation (House Prices Indexed, Inflation YoY)",
        xaxis_title="Quarter",
        yaxis_title="Index (House Prices base=100, Inflation 100 = 0%)",
        hovermode="x unified",
        legend_title="",
        margin=dict(l=0, r=0, t=50, b=0)
    )

    st.plotly_chart(fig, width='stretch')

def county_trends(df):
    st.subheader("County House Price Trends")

    counties = st.multiselect(
        "Select counties",
        sorted(df["County"].unique()),
        default=["Dublin", "Belfast"] if "Belfast" in df["County"].values else None
    )

    if not counties:
        st.info("Please select at least one county")
        return

    county_df = df[df["County"].isin(counties)]

    price_fig = px.line(
        county_df,
        x="Period",
        y="avg_price",
        color="County",
        title="Average House Prices Over Time",
        labels={"avg_price": "Average Price (€)"}
    )

    price_fig.update_layout(
        hovermode="x unified",
        margin=dict(l=0, r=0, t=50, b=0)
    )

    st.plotly_chart(price_fig, width='stretch')

    # Bar chart
    st.subheader("Cumulative Transactions by Year")

    # Aggregate annuall transactions
    annual_tx = (
        county_df
        .groupby(["County", "Year"], as_index=False)
        .agg(yearly_transactions=("transaction_count", "sum"))
        .sort_values(["County", "Year"])
    )

    # Cumulative sum per county
    annual_tx["cumulative_transactions"] = (
        annual_tx
        .groupby("County")["yearly_transactions"]
        .cumsum()
    )

    # Bar chart
    tx_fig = px.bar(
        annual_tx,
        x="Year",
        y="cumulative_transactions",
        color="County",
        barmode="group" if len(counties) > 1 else "relative",
        title="Cumulative Property Transactions Over Time",
        labels={
            "cumulative_transactions": "Cumulative Transactions",
            "Year": "Year"
        }
    )

    tx_fig.update_layout(
        hovermode="x unified",
        margin=dict(l=0, r=0, t=50, b=0)
    )

    st.plotly_chart(tx_fig, width='stretch')

def top_movers(df, metric_col, period_label):
    ranked = (
        df[["County", metric_col]]
        .dropna()
        .sort_values(metric_col, ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Top 5 Rising – {period_label}")
        st.dataframe(
            ranked.head(5)
            .rename(columns={metric_col: "Change (%)"})
            .style.format({"Change (%)": "{:.2f}"}),
            use_container_width=True
        )

    with col2:
        st.subheader(f"Top 5 Falling – {period_label}")
        st.dataframe(
            ranked.tail(5)
            .sort_values(metric_col)
            .rename(columns={metric_col: "Change (%)"})
            .style.format({"Change (%)": "{:.2f}"}),
            use_container_width=True
        )

def growth_vs_inflation(df):
    st.subheader("House Price Growth vs Inflation")

    metric = st.radio(
        "Growth Metric",
        ["QoQ", "YoY"],
        horizontal=True
    )

    metric_col = "price_qoq_pct" if metric == "QoQ" else "price_yoy_pct"

    chart_df = (
        df.groupby(["Region", "Period"])
        .agg(
            price_growth=(metric_col, "mean"),
            inflation=("Inflation_Rate", "mean")
        )
        .reset_index()
    )

    fig = px.line(
        chart_df,
        x="Period",
        y=["price_growth", "inflation"],
        color="Region",
        facet_row="variable",
        title="House Price Growth vs Inflation",
        labels={"value": "%"}
    )

    st.plotly_chart(fig, use_container_width='stretch')