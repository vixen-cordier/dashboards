import numpy as np
import pandas as pd
import streamlit as st
st.set_page_config(layout="wide", page_title="Portfolio Cordier")
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from api import *

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
            rows['Cash %'] = "{:.1f} %".format(rows['Cash'] / rows['Value'] * 100)
            rows['PnL %'] = "{:.1f} %".format(rows['PnL'] / rows['Invested'] * 100)
            rows['Value'] = "{:.0f} €".format(rows['Value'])
            rows['Invested'] = "{:.0f} €".format(rows['Invested'])
            rows['Cash'] = "{:.0f} €".format(rows['Cash'])
            rows['PnL'] = "{:.0f} €".format(rows['PnL'])
            rows['Deposited'] = "{:.0f} €".format(rows['Deposited'])
            st.dataframe(pd.DataFrame(rows, index=['All'])[['Value', 'Invested', 'Cash', 'Cash %', 'PnL', 'PnL %', 'Deposited']], use_container_width=True)

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
            st.markdown('---')
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
                rows[ptf]['Cash %'] = "{:.1f} %".format(rows[ptf]['Cash'] / rows[ptf]['Value'] * 100)
                rows[ptf]['PnL %'] = "{:.1f} %".format(rows[ptf]['PnL'] / rows[ptf]['Invested'] * 100)
                rows[ptf]['Value'] = "{:.0f} €".format(rows[ptf]['Value'])
                rows[ptf]['Invested'] = "{:.0f} €".format(rows[ptf]['Invested'])
                rows[ptf]['Cash'] = "{:.0f} €".format(rows[ptf]['Cash'])
                rows[ptf]['PnL'] = "{:.0f} €".format(rows[ptf]['PnL'])
                rows[ptf]['Deposited'] = "{:.0f} €".format(rows[ptf]['Deposited'])
            st.dataframe(pd.DataFrame(rows).transpose()[['Value', 'Invested', 'Cash', 'Cash %', 'PnL', 'PnL %', 'Deposited']], use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            # Metrics line graph
            metric = st.radio(' ', ['Value', 'Invested', 'PnL'], horizontal=True, key=f'Portofolio graph')
            st.subheader("Portfolio metrics time evolution")
            fig = go.Figure()
            for ptf in PTFS:
                fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, CLASSES, :, metric+"EUR"]].sum(axis=1).values, name=ptf))
            st.plotly_chart(fig, use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            st.subheader("Portfolio value repartition")
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
                fig = go.Figure()
                for ptf in PTFS:
                    fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, CLASSES, :, 'ValueEUR']].sum(axis=1).values, 
                                            name=ptf, stackgroup='one', groupnorm='percent'))
                st.plotly_chart(fig, use_container_width=True) 


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            st.subheader("Portfolio performance")
            value = []
            label = []
            for ptf in PTFS:
                value.append(data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'PnLEUR']].sum())
                label.append(ptf)
            fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
            st.plotly_chart(fig, use_container_width=True)


            # ========================================================================
            st.markdown('---')
            st.header("Classes")
            # Datatable
            rows = {}
            for classs in CLASSES:
                rows[classs] = {
                    'Value': data.iloc[-1].loc[pd.IndexSlice[:, classs, :, 'ValueEUR']].sum(),
                    'Invested': data.iloc[-1].loc[pd.IndexSlice[:, classs, :, 'InvestedEUR']].sum(),
                    'PnL': data.iloc[-1].loc[pd.IndexSlice[:, classs, :, 'PnLEUR']].sum(),
                }
                rows[classs]['PnL %'] = "{:.1f} %".format(rows[classs]['PnL'] / rows[classs]['Invested'] * 100)
                rows[classs]['Value'] = "{:.0f} €".format(rows[classs]['Value'])
                rows[classs]['Invested'] = "{:.0f} €".format(rows[classs]['Invested'])
                rows[classs]['PnL'] = "{:.0f} €".format(rows[classs]['PnL'])
            st.dataframe(pd.DataFrame(rows).transpose()[['Value', 'Invested', 'PnL', 'PnL %']], use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            # Metrics line graph
            metric = st.radio(' ', ['Value', 'Invested', 'PnL'], horizontal=True, key=f'Class graph')
            st.subheader("Class metrics time evolution")
            fig = go.Figure()
            for classs in CLASSES:
                fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[:, classs, :, metric+"EUR"]].sum(axis=1).values, name=classs))
            st.plotly_chart(fig, use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            st.subheader("Class value repartition")
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
                fig = go.Figure()
                for classs in CLASSES:
                    fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[:, classs, :, 'ValueEUR']].sum(axis=1), 
                                            name=classs, stackgroup='one', groupnorm='percent'))
                st.plotly_chart(fig, use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            st.subheader("Class performance")
            value = []
            label = []
            for classs in CLASSES:
                value.append(data.iloc[-1].loc[pd.IndexSlice[:, classs, :, 'PnLEUR']].sum())
                label.append(classs)
            fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
            st.plotly_chart(fig, use_container_width=True)


        else:
            ptf = PTFS[i-1]

            # ========================================================================
            st.header(f"{ptf} overview")
            # Datatable
            rows = {
                'Value': data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'ValueEUR']].sum(),
                'Invested': data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES_NOCASH, :, 'InvestedEUR']].sum(),
                'Cash': data.iloc[-1].loc[pd.IndexSlice[ptf, 'Cash', :, 'ValueEUR']].sum(),
                'PnL': data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'PnLEUR']].sum(),
                'Deposited': -data.iloc[-1].loc[pd.IndexSlice[ptf, 'Deposit', :, 'InvestedEUR']].sum(),
            }
            rows['Cash %'] = "{:.1f} %".format(rows['Cash'] / rows['Value'] * 100)
            rows['PnL %'] = "{:.1f} %".format(rows['PnL'] / rows['Invested'] * 100)
            rows['Value'] = "{:.0f} €".format(rows['Value'])
            rows['Invested'] = "{:.0f} €".format(rows['Invested'])
            rows['Cash'] = "{:.0f} €".format(rows['Cash'])
            rows['PnL'] = "{:.0f} €".format(rows['PnL'])
            rows['Deposited'] = "{:.0f} €".format(rows['Deposited'])
            st.dataframe(pd.DataFrame(rows, index=['All'])[['Value', 'Invested', 'Cash', 'Cash %', 'PnL', 'PnL %', 'Deposited']], use_container_width=True)

            # Metrics line graph
            rows = {
                'Value': data.loc[:, pd.IndexSlice[ptf, CLASSES, :, 'ValueEUR']].sum(axis=1),
                'Invested': data.loc[:, pd.IndexSlice[ptf, CLASSES_NOCASH, :, 'InvestedEUR']].sum(axis=1),
                'Cash': data.loc[:, pd.IndexSlice[ptf, 'Cash', :, 'ValueEUR']].sum(axis=1),
                'PnL': data.loc[:, pd.IndexSlice[ptf, CLASSES, :, 'PnLEUR']].sum(axis=1),
                'Deposited': -data.loc[:, pd.IndexSlice[ptf, 'Deposit', :, 'InvestedEUR']].sum(axis=1),
            }
            fig = go.Figure()
            for metric in rows:
                fig.add_trace(go.Scatter(x=rows[metric].index, y=rows[metric].values, name=metric))
            st.plotly_chart(fig, use_container_width=True)


            # ========================================================================
            st.markdown('---')
            st.header(f"{ptf} classes")
            # Datatable
            rows = {}
            for classs in CLASSES:
                rows[classs] = {
                    'Value': data.iloc[-1].loc[pd.IndexSlice[ptf, classs, :, 'ValueEUR']].sum(),
                    'Invested': data.iloc[-1].loc[pd.IndexSlice[ptf, classs, :, 'InvestedEUR']].sum(),
                    'PnL': data.iloc[-1].loc[pd.IndexSlice[ptf, classs, :, 'PnLEUR']].sum(),
                }
                rows[classs]['PnL %'] = "{:.1f} %".format(rows[classs]['PnL'] / rows[classs]['Invested'] * 100)
                rows[classs]['Value'] = "{:.0f} €".format(rows[classs]['Value'])
                rows[classs]['Invested'] = "{:.0f} €".format(rows[classs]['Invested'])
                rows[classs]['PnL'] = "{:.0f} €".format(rows[classs]['PnL'])
            st.dataframe(pd.DataFrame(rows).transpose()[['Value', 'Invested', 'PnL', 'PnL %']], use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            # Metrics line graph
            metric = st.radio(' ', ['Value', 'Invested', 'PnL'], horizontal=True, key=f'{ptf} class graph')
            st.subheader(f"{ptf} class metrics time evolution")
            fig = go.Figure()
            for classs in CLASSES:
                fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, classs, :, metric+"EUR"]].sum(axis=1).values, name=classs))
            st.plotly_chart(fig, use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            st.subheader(f"{ptf} class value repartition")
            pie_col, _, lin_col = st.columns([2, 1, 4])
            
            # Pie chart
            with pie_col:
                value = []
                label = []
                for classs in CLASSES:
                    value.append(data.iloc[-1].loc[pd.IndexSlice[ptf, classs, :, 'ValueEUR']].sum())
                    label.append(classs)
                fig = go.Figure(go.Pie(values=value, labels=label))
                st.plotly_chart(fig, use_container_width=True)

            # Line graph
            with lin_col:
                fig = go.Figure()
                for classs in CLASSES:
                    fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, classs, :, 'ValueEUR']].sum(axis=1), 
                                            name=classs, stackgroup='one', groupnorm='percent'))
                st.plotly_chart(fig, use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            st.subheader(f"{ptf} class performance")
            value = []
            label = []
            for classs in CLASSES:
                value.append(data.iloc[-1].loc[pd.IndexSlice[ptf, classs, :, 'PnLEUR']].sum())
                label.append(classs)
            fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
            st.plotly_chart(fig, use_container_width=True)


            # ========================================================================
            st.markdown('---')
            st.header(f"{ptf} assets")
            # Datatable
            rows = {}
            for (ptf, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'Market']].index:
                rows[classs, asset] = {
                    'Market': data.iloc[-1][ptf, classs, asset, 'Market'],
                    'PRU': data.iloc[-1][ptf, classs, asset, 'PRU'],
                    'Position': data.iloc[-1][ptf, classs, asset, 'Position'],
                    'Value': data.iloc[-1][ptf, classs, asset, 'Value'],
                    'Invested': data.iloc[-1][ptf, classs, asset, 'Invested'],
                    'PnL': data.iloc[-1][ptf, classs, asset, 'PnL'],
                }
                rows[classs, asset]['PnL %'] = "{:.1f} %".format(rows[classs, asset]['PnL'] / rows[classs, asset]['Invested'] * 100)
                rows[classs, asset]['Market'] = assets.loc[asset]['PriceFmt'].format(rows[classs, asset]['Market'])
                rows[classs, asset]['PRU'] = assets.loc[asset]['PriceFmt'].format(rows[classs, asset]['PRU'])
                rows[classs, asset]['Position'] = assets.loc[asset]['PositionFmt'].format(rows[classs, asset]['Position'])
                rows[classs, asset]['Value'] = assets.loc[asset]['ValueFmt'].format(rows[classs, asset]['Value'])
                rows[classs, asset]['Invested'] = assets.loc[asset]['ValueFmt'].format(rows[classs, asset]['Invested'])
                rows[classs, asset]['PnL'] = assets.loc[asset]['ValueFmt'].format(rows[classs, asset]['PnL'])
            st.dataframe(pd.DataFrame(rows).transpose()[['Market', 'PRU', 'Position', 'Value', 'Invested', 'PnL', 'PnL %']], use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            # Metrics line graph
            metric = st.radio(' ', ['Value', 'Invested', 'PnL'], horizontal=True, key=f'{ptf} asset graph')
            st.subheader(f"{ptf} asset metrics time evolution")
            fig = go.Figure()
            for (ptf, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'Market']].index:
                fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, classs, asset, metric+"EUR"]].values, name=asset))
            st.plotly_chart(fig, use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            st.subheader(f"{ptf} asset value repartition")
            pie_col, _, lin_col = st.columns([2, 1, 4])
            
            # Pie chart
            with pie_col:
                value = []
                label = []
                for (ptf, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'Market']].index:
                    value.append(data.iloc[-1].loc[pd.IndexSlice[ptf, classs, asset, 'ValueEUR']])
                    label.append(asset)
                fig = go.Figure(go.Pie(values=value, labels=label))
                st.plotly_chart(fig, use_container_width=True)

            # Line graph
            with lin_col:
                fig = go.Figure()
                for (ptf, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'Market']].index:
                    fig.add_trace(go.Scatter(x=data.index, y=data.loc[:, pd.IndexSlice[ptf, classs, asset, 'ValueEUR']], 
                                            name=asset, stackgroup='one', groupnorm='percent'))
                st.plotly_chart(fig, use_container_width=True)


            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            st.subheader(f"{ptf} asset performance")
            value = []
            label = []
            for (ptf, classs, asset, _) in data.iloc[-1].loc[pd.IndexSlice[ptf, CLASSES, :, 'Market']].index:
                value.append(data.iloc[-1].loc[pd.IndexSlice[ptf, classs, asset, 'PnLEUR']])
                label.append(asset)
            fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
            st.plotly_chart(fig, use_container_width=True)