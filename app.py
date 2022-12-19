import streamlit as st
import gspread as gs 
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from typing import Dict


# ----------------------------------------------
# Get data, concate, merge and extract metrics
# for portfolio Dashboard 
# ----------------------------------------------

### Connect to Google Sheet
gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
ss = gc.open_by_key(st.secrets['portfolio'].spreadsheet_key)
ws_operation = ss.worksheet('Operations')
ws_greenbull = ss.worksheet('GREENBULL')
ws_dict = ss.worksheet('Dict')


### Get asset list and fetch data fom yahoo finance
greenbull = pd.DataFrame(ws_greenbull.get_all_records()).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')
dict = pd.DataFrame(ws_dict.get_all_records())

assets: Dict[str,str] = dict[['Asset', 'Market', 'Currency']].set_index('Asset').to_dict()
print(assets['Market'])
print(assets['Currency'])
market = yf.download(' '.join(list(assets['Market'].values())[:-1]), start='2021-04-01')['Close']
market = pd.concat([market, greenbull], axis=1)
market = pd.concat([market], keys=['Market'], axis=1)
market = pd.concat([market], keys=['Cotation'], axis=1)

depots: Dict[str,str] = dict[['Depot', 'Forex']].set_index('Depot').to_dict()
print(depots['Forex'])
forex: pd.DataFrame = yf.download(' '.join(list(depots['Forex'].values())), start='2021-04-01')['Close']
forex = pd.concat([forex], keys=['Forex'], axis=1)
forex = pd.concat([forex], keys=['Cotation'], axis=1)

df = pd.concat([market, forex], axis=1).ffill().bfill()


### Get all operation from Spreadsheet, merge and calculate all portfolio metrics
ope = pd.DataFrame(ws_operation.get_all_records()).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')

for portfolio in np.unique(ope['Portfolio']):
    dfp: pd.DataFrame = ope[ope['Portfolio'] == portfolio]
    print('', portfolio)

    for asset in np.unique(dfp['Asset']):
        dfa: pd.DataFrame = dfp[dfp['Asset'] == asset]
        dfa = dfa.groupby('Date').agg({'Amount': "sum", 'Total': "sum"})#, 'TotalEUR': "sum"})
        print('  ', asset)

        amt, tot = pd.Series(dtype=float), pd.Series(dtype=float)
        for idx in dfa.index:
            amt[idx] = np.sum(dfa.loc[:idx]['Amount'])
            tot[idx] = np.sum(dfa.loc[:idx]['Total'])

        if asset in assets['Market'].keys():
            df = pd.concat([df, pd.DataFrame({
                ('Position', portfolio, asset): amt,
                ('Invested', portfolio, asset): tot,
            })], axis=1).ffill().fillna(0)

            df['InvestedEUR', portfolio, asset] = df['Invested', portfolio, asset] * df['Cotation', 'Forex', depots['Forex'][assets['Currency'][asset]]]
            df['PRU', portfolio, asset] = df['Invested', portfolio, asset] / df['Position', portfolio, asset]
            df['Value', portfolio, asset] = df['Position', portfolio, asset] * df['Cotation', 'Market', assets['Market'][asset]]
            df['ValueEUR', portfolio, asset] = df['Value', portfolio, asset] * df['Cotation', 'Forex', depots['Forex'][assets['Currency'][asset]]]
            df['PnL', portfolio, asset] = df['Value', portfolio, asset] - df['Invested', portfolio, asset]
            df['PnLEUR', portfolio, asset] = df['PnL', portfolio, asset] * df['Cotation', 'Forex', depots['Forex'][assets['Currency'][asset]]]

        elif asset in depots['Forex'].keys():
            df = pd.concat([df, pd.DataFrame({
                ('Amount', portfolio, asset): amt,
                ('Deposit', portfolio, asset): tot,
            })], axis=1).ffill().fillna(0)

            df['DepositEUR', portfolio, asset] = df['Deposit', portfolio, asset] * df['Cotation', 'Forex', depots['Forex'][asset]]
            # df['PnL', portfolio, asset] = df['Deposit', portfolio, asset] - df['DepositEUR', portfolio, asset]
            # df['PnLEUR', portfolio, asset] = df['PnL', portfolio, asset] * df['Cotation', 'Forex', depots['Forex'][asset]]
            
    if 'DepositEUR' in df.columns and portfolio in df['DepositEUR'].columns:
        df['DepositEUR', portfolio, 'All'] = df['DepositEUR', portfolio].sum(axis=1)
    if 'InvestedEUR' in df.columns and portfolio in df['InvestedEUR'].columns:
        df['InvestedEUR', portfolio, 'All'] = df['InvestedEUR', portfolio].sum(axis=1)
    if 'ValueEUR' in df.columns and portfolio in df['ValueEUR'].columns:
        df['ValueEUR', portfolio, 'All'] = df['ValueEUR', portfolio].sum(axis=1)
    if 'PnLEUR' in df.columns and portfolio in df['PnLEUR'].columns:
        df['PnLEUR', portfolio, 'All'] = df['PnLEUR', portfolio].sum(axis=1)


# ----------------------------------------------
# Dashboard construction
# by Streamlit
# ----------------------------------------------
st.set_page_config(layout="wide")
st.title("Portfolio Dashboard")

portfo = st.selectbox(
    "Select portfolio",
    ("Email", "Home phone", "Mobile phone")
)

metric = st.radio(
    "Set selectbox label visibility ??",
    key="visibility",
    options=["visible", "hidden", "collapsed"],
)

tab1, tab2, tab3 = st.tabs(["Overview", "Assets", "Data"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['DepositEUR', 'ZEN', 'All'], name='Deposit'))
    fig.add_trace(go.Scatter(x=df.index, y=df['InvestedEUR', 'ZEN', 'All'], name='Invested'))
    fig.add_trace(go.Scatter(x=df.index, y=df['ValueEUR', 'ZEN', 'All'], name='Value'))
    fig.add_trace(go.Scatter(x=df.index, y=df['PnLEUR', 'ZEN', 'All'], name='PnL'))
    # for asset in df['PnLEUR', 'ZEN'].columns:
    #     print(asset)
    #     fig.add_trace(go.Scatter(x=df.index, y=df['PnLEUR', 'ZEN', asset], name=asset))
    st.plotly_chart(fig)

with tab2:
    fig = go.Figure()
    for asset in df['PnLEUR', 'ZEN'].columns:
        print(asset)
        fig.add_trace(go.Scatter(x=df.index, y=df['PnLEUR', 'ZEN', asset], name=asset))
    st.plotly_chart(fig)

with tab3:
   st.header("An owl")
   st.image("https://static.streamlit.io/examples/owl.jpg", width=200)


with st.expander("Operation spreadcheet"):
    st.write(ope)