import streamlit as st

def county_rankings(df, metric_col, period_label):
    ranked = (
        df[["County", metric_col]]
        .dropna()
        .sort_values(metric_col, ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 5 Rising")
        st.dataframe(
            ranked.head(5)
            .rename(columns={metric_col: "Change (%)"})
            .style.format({"Change (%)": "{:.2f}"}),
            use_container_width=True
        )

    with col2:
        st.subheader("Top 5 Falling")
        st.dataframe(
            ranked.tail(5)
            .sort_values(metric_col)
            .rename(columns={metric_col: "Change (%)"})
            .style.format({"Change (%)": "{:.2f}"}),
            use_container_width=True
        )
