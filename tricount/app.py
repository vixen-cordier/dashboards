import numpy as np
import pandas as pd
import streamlit as st
st.set_page_config(layout="wide", page_title="Tricount Cocon")
import plotly.graph_objects as go
import warnings
warnings.simplefilter(action='ignore', category=pd.core.common.SettingWithCopyWarning)
warnings.simplefilter(action='ignore', category=RuntimeWarning)

from api import *

# @st.cache_data
@st.experimental_memo
def get_data():
    return build_data()

operations, categories, postes, result = get_data()

PEOPLES = ['Total', 'Lucie', 'Vincent']
periods = []
with st.sidebar:
    people = st.radio("Choose", PEOPLES)
    st.markdown('---')
    for period in categories.keys():
        if st.checkbox(period):
            periods.append(period)


print("""
    # --------------------------------- #
    # Build screen elements             #
    # --------------------------------- #
""")


st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

st.title(f"Tricount Dashboard : {people}")
# title, refresh = st.columns([9, 1])
# with title:
#     st.title(f"Tricount Dashboard : {people}")
# with refresh:
#     if st.button('Refresh'):
#         st.cache_data.clear()


if len(periods) == 0:
    st.write('Tick the periods')
else:
    st.header("Overview")
    period_graph = st.radio('Period for graph', periods, horizontal=True, key=f'{people} graph key', label_visibility='collapsed')

    df = pd.concat([
        result[period_graph][people][['Revenus']],
        -result[period_graph][people][['Dépenses']],
        -postes[period_graph][people][['Quotidien', 'Achats', 'Extra', 'Loisir']],
        result[period_graph][people][['Reste à vivre', 'Capital investi']],
        -postes[period_graph][people][['Investissement', 'Formation']],
        result[period_graph][people][['Epargne']],
    ])
    colors = ['green', 'firebrick', 'chocolate', 'chocolate', 'chocolate', 'chocolate', 'goldenrod', 'dodgerblue', 'skyblue', 'skyblue','gold']
    st.plotly_chart(go.Figure(go.Bar(x=df.index.to_list(), y=df.values, marker_color=colors))
    .update_layout(height=450), use_container_width=True)

    col1, _, col2 = st.columns([4,1,4])
    with col1:
        st.subheader("Répartition des revenus")
        df = pd.concat([
            -result[period_graph][people][['Dépenses']],
            result[period_graph][people][['Capital investi', 'Epargne']],
        ])
        colors = ['firebrick', 'dodgerblue', 'gold']
        colors_bis = colors.copy()
        for i in reversed(range(0,df.shape[0])):
            if df[i] <= 0:
                st.write(f"/!\ {df.index[i]} = {df[i]} € <= 0")
                df = df.drop(df.index[i])
                colors.remove(colors_bis[i])  
        st.plotly_chart(go.Figure(go.Pie(values=df.values, labels=df.index.to_list(), marker=dict(colors=colors))), use_container_width=True)

    with col2:
        st.subheader("Catégories de dépense")
        df = pd.concat([
            -postes[period_graph][people][['Quotidien', 'Achats', 'Extra', 'Loisir']],
            result[period_graph][people][['Reste à vivre']],
        ])
        colors = ['chocolate', 'saddlebrown', 'sienna', 'peru', 'goldenrod']
        colors_bis = colors.copy()
        for i in reversed(range(0,df.shape[0])):
            if df[i] <= 0:
                st.write(f"/!\ {df.index[i]} = {df[i]} € <= 0")
                df = df.drop(df.index[i])
                colors.remove(colors_bis[i]) 
        st.plotly_chart(go.Figure(go.Pie(values=df.values, labels=df.index.to_list(), marker=dict(colors=colors))), use_container_width=True)


    st.subheader("Synthèse")
    table, graph = st.tabs(['Table', 'Graph'])
    rows = {}
    for period in periods:
        rows[period] = result[period][people]
    df = pd.concat(rows, axis=1).transpose()

    with table:
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
    with graph:
        fig = go.Figure()
        for metric in [m for m in df.columns if m in ['Revenus', 'Dépenses', 'Reste à vivre', 'Capital investi', 'Epargne']]:
            fig.add_trace(go.Scatter(x=df.index.tolist()[::-1], y=np.abs(df[metric].values.tolist()[::-1]), name=metric))
        st.plotly_chart(fig)

    st.subheader("Budget")
    rows = {}
    for period in periods:
        rows[period] = postes[period][people]
    table, graph = st.tabs(['Table', 'Graph'])

    with table:
        df = pd.concat(rows, axis=1).transpose()
        st.table(df
            .style
            .format("{:.0f} €")
            .highlight_null(props="color: transparent;")
            .bar(subset=df.columns, color=['#d65f5f77', '#5fba7d77'])# if draw_bar else ['#00000000', '#00000000'])
        )
    with graph:
        fig = go.Figure()
        for metric in df.columns:
            fig.add_trace(go.Scatter(x=df.index.tolist()[::-1], y=np.abs(df[metric].values.tolist()[::-1]), name=metric))
        st.plotly_chart(fig)


    st.markdown('---')
    st.header(f"Categories : {people}")
    rows = {}
    for i, period in enumerate(periods):
        rows[period] = categories[period][people]
    st.dataframe(pd.concat(rows, axis=1).style.format("{:.0f}").highlight_null(props="color: transparent;"), height=850)

    st.markdown('---')
    st.header("All operations")
    df = pd.DataFrame(columns=operations.columns)
    for i, period in enumerate(periods):
        df = pd.concat([df, operations[operations['Period'] == period]])
    st.dataframe(df[['Date', 'Titre', 'Poste', 'Catégorie', 'Payé par', 'Impacté à Lucie', 'Impacté à Vincent']], use_container_width=True)


