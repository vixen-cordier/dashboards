import numpy as np
import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")
import plotly.graph_objects as go
import warnings
warnings.simplefilter(action='ignore', category=pd.core.common.SettingWithCopyWarning)

from api_tricount import * 


@st.experimental_memo 
def get_data():
    data, dict = fetch_data()
    data = build_data(data)
    detail = split_data(data, dict)
    postes, result = concat_data(detail, dict)
    return detail, postes, result 

detail, postes, result = get_data()

print("""
    # --------------------------------- #
    # Build screen elements             #
    # --------------------------------- #
""")


st.title("Tricount Dashboard")

people_x = {}
period_x = {}
with st.sidebar:
    for people in ['Total', 'Lucie', 'Vincent']:
        people_x[people] = st.checkbox(people, value=True)
    st.markdown('---')
    for period in detail.keys():
        period_x[period] = st.checkbox(period)

peoples = [people for people, check in people_x.items() if check==True]
periods = [period for period, check in period_x.items() if check==True]

if len(periods) == 0:
    st.write('Tick the periods')
else:
    for people in peoples:
        # col1, col2 = st.columns(2)
        # with col1:
        # with col2:
        #     draw_bar = st.checkbox("Draw bars", value=True)
        st.subheader(people)


        period = st.radio('Graph', periods, horizontal=True, key=f'{people} graph key')
        # col1, col2 = st.columns([1, 3])
        col1, _, col2 = st.columns([4,1,4])
       
        with col1:
            df: pd.DataFrame = -postes[period][people][['Quotidien', 'Achats', 'Extra', 'Loisir']]
            df['Reste à vivre'] = result[period][people]['Reste à vivre']
            st.plotly_chart(go.Figure(go.Pie(values=df.values, labels=df.index.to_list())), use_container_width=True)
        with col2:
            df: pd.DataFrame = result[period][people][['Revenus', 'Dépenses', 'Capital investi', 'Epargne']]
            # df: pd.DataFrame = result[period][people][['Dépenses', 'Capital investi', 'Epargne']]
            # df = df.abs()
            st.plotly_chart(go.Figure(go.Bar(x=df.index.to_list(), y=df.values)).update_layout(height=450), use_container_width=True)
            # st.plotly_chart(go.Figure(go.Pie(values=df.values, labels=df.index.to_list())), use_container_width=True)



        # st.write("Graph")
        # # col1, col2 = st.columns([1, 3])
        # col1, col2, col3 = st.columns([1, 2, 2])
        # with col1:
        #     period = st.radio('',periods)
        # with col2:
        #     df: pd.DataFrame = -postes[period][people][['Quotidien', 'Achats', 'Extra', 'Loisir']]
        #     df['Reste à vivre'] = result[period][people]['Reste à vivre']
        #     st.plotly_chart(go.Figure(go.Pie(values=df.values, labels=df.index.to_list())).update_layout(height=350))
        # with col3:
        #     df: pd.DataFrame = result[period][people][['Revenus', 'Dépenses', 'Capital investi', 'Epargne']]
        #     df = df.abs()
        #     st.plotly_chart(go.Figure(go.Bar(x=df.index.to_list(), y=df.values)).update_layout(height=350))
        #     # st.plotly_chart(go.Figure(go.Bar(x=df.values, y=df.index.to_list(), orientation='h')).update_layout(height=350))


        st.write("Synthèse")
        rows = {}
        for period in periods:
            rows[period] = result[period][people]
        df = pd.concat(rows, axis=1).transpose()
        st.table(df
            .style
            .format({
                "Revenus": "{:.0f} €",
                "Dépenses": "{:.0f} €",
                "Reste à vivre": "{:.0f} €",
                "Reste à vivre %": "{:.0f} %",
                "Capital investi": "{:.0f} €",
                "Capital investi %": "{:.0f} %",
                "Epargne": "{:.0f} €",
                "Epargne %": "{:.0f} %",
            }) 
            .highlight_null(props="color: transparent;")
            .bar(subset=df.columns, color=['#d65f5f77', '#5fba7d77'])# if draw_bar else ['#00000000', '#00000000'])
        )

        st.write("Budget")
        rows = {}
        for period in periods:
            rows[period] = postes[period][people]
        df = pd.concat(rows, axis=1).transpose()
        st.table(df
            .style
            .format("{:.0f} €")
            .highlight_null(props="color: transparent;")
            .bar(subset=df.columns, color=['#d65f5f77', '#5fba7d77'])# if draw_bar else ['#00000000', '#00000000'])
        )

    st.markdown('---')
    st.subheader("Détails des catégories")
    rows = {}
    for i, period in enumerate(periods):
        if len(peoples) > 1:
            rows[i] = pd.Series(dtype='int')
        rows[period] = detail[period][peoples]
    st.table(pd.concat(rows, axis=1).style.format("{:.0f}").highlight_null(props="color: transparent;"))

    # cols = st.columns(len(periods))
    # for i, col in enumerate(cols):
    #     with col:
    #         st.subheader(periods[i])
    #         df = detail[periods[i]][peoples]
    #         if i == 0:
    #             st.table(df.style.format("{:.0f}").highlight_null(props="color: transparent;"))
    #         else:
    #             st.table(df.style.hide(axis=0).format("{:.0f}").highlight_null(props="color: transparent;"))
