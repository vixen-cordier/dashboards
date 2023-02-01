import pandas as pd
import calendar as cd
import streamlit as st
import plotly.graph_objects as go

from api_tricount import build_data
data = build_data()


st.set_page_config(layout="wide")
st.title("Tricount Dashboard")
st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    # font-weight: bold;
    font-size: 24px; 
}
</style>
""", unsafe_allow_html=True)






years = ["2023", "2022", "2021"]

for i, year_tab in enumerate(st.tabs(years)):
    with year_tab:
        df = data.loc[int(years[i]),:,:]
        months = df.index.get_level_values('Mois').unique().tolist()
        yearly_average, monthly_detail = st.columns(2)
        with yearly_average:
            st.header("Yearly Average")
            st.dataframe(pd.DataFrame(df.groupby('Catégorie').sum()/len(months)).style.format("{:.2f}"))
        with monthly_detail:
            print(months)
            st.header("Monthly Detail")
            for j, month_tab in enumerate(st.tabs([cd.month_name[month] for month in months])):
                print(j, month_tab)
                with month_tab:
                    st.write(months[j])
