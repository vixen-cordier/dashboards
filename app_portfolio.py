import numpy as np
import pandas as pd
import streamlit as st
st.set_page_config(layout="wide", page_title="Portfolio Cordier")
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from api_portfolio import build_data

@st.experimental_memo
def get_data(): 
    return build_data()

data, assets = get_data()

st.title("Portfolio Dashboard")
st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    # font-weight: bold;
    font-size: 24px;
}
</style>
""", unsafe_allow_html=True)


# def datatable(s: pd.Series):
# def datatable_ptf(s: pd.Series, PTFS):
# def datatable_asset(s: pd.Series, ptf):

# def scatter(df):
# def scatter_ptf(df, ptf):
# def scatter_PTFS(df, PTFS, metric):
# def scatter_asset(df, ptf, metric):

# def pie_ptf(s, PTFS):
# def pie_class(s, ptf):
# def pie_asset(s, ptf):

# def stack_ptf(df, PTFS):
# def stack_class(df, ptf):
# def stack_asset(df, ptf):



def bar_ptf(s, PTFS):
    value = []
    label = []
    for ptf in PTFS:
        value.append(s['PnLEUR', ptf, 'All'])
        label.append(ptf)
    fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
    st.plotly_chart(fig, use_container_width=True)

def bar_asset(s, ptf):
    value = []
    label = []
    for asset in s['ValueEUR', ptf, :].index:
        if asset != 'All':
            value.append(s['PnLEUR', ptf, asset])
            label.append(asset)
    fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
    st.plotly_chart(fig, use_container_width=True)




PTFS = np.unique(data.columns.get_level_values(0))
CLASSES = ['Cash', 'Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income']
CLASSES_NOCASH = ['Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income']

tabs = st.tabs(["All", *PTFS])
for i, tab in enumerate(tabs):
    with tab:
        if i == 0:

            # ========================================================================
            st.header("Overview")
            # Datatable
            rows = {
                'Value': data.iloc[-1].loc[pd.IndexSlice[:, CLASSES, :, 'ValueEUR']].sum(),
                'Invested': data.iloc[-1].loc[pd.IndexSlice[:, CLASSES_NOCASH, :, 'InvestedEUR']].sum(),
                'Cash': data.iloc[-1].loc[pd.IndexSlice[:, 'Cash', :, 'ValueEUR']].sum(),
                'PnL': data.iloc[-1].loc[pd.IndexSlice[:, CLASSES, :, 'PnLEUR']].sum(),
                'Deposited': -data.iloc[-1].loc[pd.IndexSlice[:, 'Deposit', :, 'InvestedEUR']].sum(),
            }
            df = pd.DataFrame(rows, index=['All'])#.transpose()[['Value', 'Invested', 'Cash', 'PnL', 'Deposited']]
            st.dataframe(df.style.format("{:.0f} €"), use_container_width=True)

            # Metrics line graph
            rows = {
                'Value': data.loc[:, pd.IndexSlice[:, CLASSES, :, 'ValueEUR']].sum(axis=1),
                'Invested': data.loc[:, pd.IndexSlice[:, CLASSES_NOCASH, :, 'InvestedEUR']].sum(axis=1),
                'Cash': data.loc[:, pd.IndexSlice[:, 'Cash', :, 'ValueEUR']].sum(axis=1),
                'PnL': data.loc[:, pd.IndexSlice[:, CLASSES, :, 'PnLEUR']].sum(axis=1),
                'Deposited': -data.loc[:, pd.IndexSlice[:, 'Deposit', :, 'InvestedEUR']].sum(axis=1),
            }
            fig = go.Figure()
            for metric in rows:
                fig.add_trace(go.Scatter(x=rows[metric].index, y=rows[metric].values, name=metric))
            st.plotly_chart(fig, use_container_width=True)


            # ========================================================================
            st.header("Portfolios")
            # Datatable
            rows = {}
            for ptf in PTFS:
                rows[ptf] = {
                    'Value': data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'ValueEUR']].sum(),
                    'Invested': data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES_NOCASH, :, 'InvestedEUR']].sum(),
                    'Cash': data.iloc[-1].loc[pd.IndexSlice[ptf, 'Cash', :, 'ValueEUR']].sum(),
                    'PnL': data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'PnLEUR']].sum(),
                    'Deposited': -data.iloc[-1].loc[pd.IndexSlice[ptf, 'Deposit', :, 'InvestedEUR']].sum(),
                }
            df = pd.DataFrame(rows).transpose()[['Value', 'Invested', 'Cash', 'PnL', 'Deposited']]
            st.dataframe(df.style.format("{:.0f} €"), use_container_width=True)

            # Metrics line graph
            metric = st.radio('Metric: ', ['ValueEUR', 'InvestedEUR', 'PnLEUR'], horizontal=True, key=f'Portofolio graph')
            fig = go.Figure()
            for ptf in PTFS:
                fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, CLASSES, :, metric]].sum(axis=1).values, name=ptf))
            st.plotly_chart(fig, use_container_width=True)


            # ========================================================================
            st.subheader("Portfolio repartition")
            pie_col, _, lin_col = st.columns([2, 1, 4])
            
            # Pie chart
            with pie_col:
                value = []
                label = []
                for ptf in PTFS:
                    value.append(data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'ValueEUR']].sum())
                    label.append(ptf)
                fig = go.Figure(go.Pie(values=value, labels=label))
                st.plotly_chart(fig, use_container_width=True)

            # Line graph
            with lin_col:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                for ptf in PTFS:
                    fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, CLASSES, :, 'ValueEUR']].sum(axis=1).values, 
                                            name=ptf, stackgroup='one', groupnorm='percent'))
                    # fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, CLASSES, :, 'ValueEUR']].sum(axis=1).values, 
                    #                         name=ptf), secondary_y=True)
                # fig.update_yaxes(rangemode='tozero')
                st.plotly_chart(fig, use_container_width=True) 


            # ========================================================================
            st.subheader("Portfolio class repartition")
            pie_col, _, lin_col = st.columns([2, 1, 4])
            
            # Pie chart
            with pie_col:
                value = []
                label = []
                for classs in CLASSES:
                    value.append(data.iloc[-1].loc[pd.IndexSlice[:, classs, :, 'ValueEUR']].sum())
                    label.append(classs)
                fig = go.Figure(go.Pie(values=value, labels=label))
                st.plotly_chart(fig, use_container_width=True)

            # Line graph
            with lin_col:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                for classs in CLASSES:
                    fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[:, classs, :, 'ValueEUR']].sum(axis=1), 
                                            name=classs, stackgroup='one', groupnorm='percent'))
                    # fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, classs, :, 'ValueEUR']].sum(axis=1), 
                    #                          name=classs), secondary_y=True)
                # fig.update_yaxes(rangemode='tozero')
                st.plotly_chart(fig, use_container_width=True)

            # ========================================================================
            st.subheader("Portfolio performance")
            # bar_ptf(data.iloc[-1], ['All', 'ZEN', 'DMA'])

        else:

            # ========================================================================
            st.header(f"{PTFS[i-1]} overview")
            # Datatable
            rows = {
                'Value': data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], CLASSES, :, 'ValueEUR']].sum(),
                'Invested': data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], CLASSES_NOCASH, :, 'InvestedEUR']].sum(),
                'Cash': data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], 'Cash', :, 'ValueEUR']].sum(),
                'PnL': data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], CLASSES, :, 'PnLEUR']].sum(),
                'Deposited': -data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], 'Deposit', :, 'InvestedEUR']].sum(),
            }
            df = pd.DataFrame(rows, index=[PTFS[i-1]])#.transpose()[['Value', 'Invested', 'Cash', 'PnL', 'Deposited']]
            st.dataframe(df.style.format("{:.0f} €"), use_container_width=True)

            # Metrics line graph 
            rows = {
                'Value': data.loc[:, pd.IndexSlice[PTFS[i-1], CLASSES, :, 'ValueEUR']].sum(axis=1),
                'Invested': data.loc[:, pd.IndexSlice[PTFS[i-1], CLASSES_NOCASH, :, 'InvestedEUR']].sum(axis=1),
                'Cash': data.loc[:, pd.IndexSlice[PTFS[i-1], 'Cash', :, 'ValueEUR']].sum(axis=1),
                'PnL': data.loc[:, pd.IndexSlice[PTFS[i-1], CLASSES, :, 'PnLEUR']].sum(axis=1),
                'Deposited': -data.loc[:, pd.IndexSlice[PTFS[i-1], 'Deposit', :, 'InvestedEUR']].sum(axis=1),
            }
            fig = go.Figure()
            for metric in rows:
                fig.add_trace(go.Scatter(x=rows[metric].index, y=rows[metric].values, name=metric))
            st.plotly_chart(fig, use_container_width=True)
            

            # # ========================================================================
            # st.header(f"{PTFS[i-1]} assets")
            # # Datatable
            # rows = {}
            # for (ptf, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], CLASSES_NOCASH, :, 'Market']].index:
            #     rows[classs, asset] = {
            #         'Market': data.iloc[-1].loc[asset]['PriceFmt'].format(data.iloc[-1][PTFS[i-1], classs, asset, 'Market']),
            #         'PRU': data.iloc[-1].loc[asset]['PriceFmt'].format(data.iloc[-1][PTFS[i-1], classs, asset, 'PRU']),
            #         'Position': data.iloc[-1].loc[asset]['PositionFmt'].format(data.iloc[-1][PTFS[i-1], classs, asset, 'Position']),
            #         'Value': data.iloc[-1].loc[asset]['ValueFmt'].format(data.iloc[-1][PTFS[i-1], classs, asset, 'Value']),
            #         'Invested': data.iloc[-1].loc[asset]['ValueFmt'].format(data.iloc[-1][PTFS[i-1], classs, asset, 'Invested']),
            #         'PnL': data.iloc[-1].loc[asset]['ValueFmt'].format(data.iloc[-1][PTFS[i-1], classs, asset, 'PnL']),
            #     }
            # df = pd.DataFrame(rows).transpose()[['Market', 'PRU', 'Position', 'Value', 'Invested', 'PnL']]
            # st.dataframe(df, use_container_width=True)

            # # Metrics line graph
            # metric = st.radio('Metric: ', ['ValueEUR', 'InvestedEUR', 'PnLEUR'], horizontal=True, key=f'ZEN asset graph')
            # fig = go.Figure()
            # for (ptf, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], CLASSES, :, metric]].index:
            #     fig.add_trace(go.Scatter(x=data.index, y=data[ptf, classs, asset, metric].values, name=asset))
            # st.plotly_chart(fig, use_container_width=True)

            # ========================================================================
            st.subheader(f"{PTFS[i-1]} class repartition")
            pie_col, _, lin_col = st.columns([2, 1, 4])
            with pie_col:
                value = []
                label = []
                for classs in CLASSES:
                    value.append(data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], classs, :, 'ValueEUR']].sum())
                    label.append(classs)
                fig = go.Figure(go.Pie(values=value, labels=label))
                st.plotly_chart(fig, use_container_width=True)

            with lin_col:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                for classs in CLASSES:
                    fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[PTFS[i-1], classs, :, 'ValueEUR']].sum(axis=1), 
                                            name=classs, stackgroup='one', groupnorm='percent'))
                    # fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, classs, :, 'ValueEUR']].sum(axis=1), 
                    #                          name=classs), secondary_y=True)
                # fig.update_yaxes(rangemode='tozero')
                st.plotly_chart(fig, use_container_width=True)

            # ========================================================================
            st.subheader(f"{PTFS[i-1]} asset repartition")
            pie_col, _, lin_col = st.columns([2, 1, 4])
            with pie_col:
                value = []
                label = []
                for (_, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], CLASSES, :, 'ValueEUR']].index:
                    value.append(data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], classs, asset, 'ValueEUR']].sum())
                    label.append(asset)
                fig = go.Figure(go.Pie(values=value, labels=label))
                st.plotly_chart(fig, use_container_width=True)
            
            with lin_col:
                fig = go.Figure()
                for (_, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[PTFS[i-1], CLASSES, :, 'ValueEUR']].index:
                    fig.add_trace(go.Scatter(x=data.index, y=data[PTFS[i-1], classs, asset, 'ValueEUR'], 
                                            name=asset, stackgroup='one', groupnorm='percent'))
                st.plotly_chart(fig, use_container_width=True)

            # ========================================================================
            st.subheader(f"{PTFS[i-1]} asset performance")
            # bar_asset(data.iloc[-1], 'ZEN')
