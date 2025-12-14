import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st
from src.data_loader import load_data
from src.maps import growth_choropleth, range_growth_choropleth #price_choropleth, change_choropleth, 
from src.charts import  county_trends, price_vs_inflation #all_island_price_vs_inflation_dual_axis,
from src.inflation import prepare_cumulative_inflation
from src.price_index import prepare_price_index
from src.price_changes import add_qoq_change, add_yoy_change
from src.rankings import county_rankings


st.set_page_config(layout="wide")
st.title("Ireland Housing Market Dashboard")

# Load data
df, geo = load_data()

# Add quarter-to-quarter and year-to-year price changes
df = add_qoq_change(df)
df = add_yoy_change(df)

# --------------------
# Prepare indexed data
# --------------------

roi = df[df["County"].isin([
    "Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry",
    "Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford","Louth",
    "Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo","Tipperary",
    "Waterford","Westmeath","Wexford","Wicklow"
])]

ni = df[~df.index.isin(roi.index)]

roi_inf = prepare_cumulative_inflation(roi)
ni_inf = prepare_cumulative_inflation(ni)

roi_price = prepare_price_index(roi)
ni_price = prepare_price_index(ni)

plot_df = pd.concat([
    roi_price.assign(
        Series="RoI House Prices",
        Value=roi_price["Price_Index"]
    )[["Period", "Value", "Series"]],

    ni_price.assign(
        Series="NI House Prices",
        Value=ni_price["Price_Index"]
    )[["Period", "Value", "Series"]],

    roi_inf.assign(
        Series="RoI Inflation",
        Value=roi_inf["Inflation_Index"]
    )[["Period", "Value", "Series"]],

    ni_inf.assign(
        Series="NI Inflation",
        Value=ni_inf["Inflation_Index"]
    )[["Period", "Value", "Series"]],
])


# --------------------
# Tabs
# --------------------

tab1, tab2, tab3, tab4 = st.tabs(
    ["Fixed Period Change", "Custom Period Change", "Inflation vs House Prices", "County Trends"]
)


with tab1:
    growth_choropleth(df, geo)

with tab2:
    range_growth_choropleth(df, geo)

with tab3:
    price_vs_inflation(df)

with tab4:
    county_trends(df)
