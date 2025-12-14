import pandas as pd
import geopandas as gpd
import streamlit as st

@st.cache_data
def load_data():
    df = pd.read_csv("data/all_island_quarterly_inflation_clean.csv")
    df = df.sort_values(["Year", "Quarter"])
    geo = gpd.read_file("data/ireland-counties.geojson")
    return df, geo
