import streamlit as st
import pandas as pd

def period_range_selector(df):
    periods = (
        df[["Year", "Quarter", "Period"]]
        .drop_duplicates()
        .sort_values(["Year", "Quarter"])
        .reset_index(drop=True)
    )

    labels = periods["Period"].tolist()

    start, end = st.select_slider(
        "Select time range",
        options=labels,
        value=(labels[0], labels[-1])
    )

    return start, end
