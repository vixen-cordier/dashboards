import streamlit as st
import gspread as gs 
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go


# ----------------------------------------------
# Get data, concate, merge and extract metrics
# for portfolio Dashboard 
# ----------------------------------------------

def extract_sheets():
    gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
    ss = gc.open_by_key(st.secrets['portfolio'].spreadsheet_key)
    dicts = pd.DataFrame(ss.worksheet('Dict').get_all_records())
    return {
        'Operation': pd.DataFrame(
            ss.worksheet('Operations').get_all_records()
            ).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')
        ,
        'Others': {
            'GREENBULL': pd.DataFrame(
                ss.worksheet('GREENBULL').get_all_records()
                ).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')
        },
        'Dicts': {
            'assets': pd.DataFrame(dicts[['Asset', 'Market', 'Currency']].set_index('Asset').to_dict()),
            'depots': pd.DataFrame(dicts[['Depot', 'Forex']].set_index('Depot').to_dict())
        }
    }


def fetch_market(assets, others):
    market = yf.download(' '.join(list(assets['Market'])[:-1]), start='2021-04-01')['Close']
    market = pd.concat([market, others['GREENBULL']], axis=1)
    market = pd.concat([market], keys=['Market'], axis=1)
    market = pd.concat([market], keys=['Cotation'], axis=1)
    return market

def fetch_forex(depots):
    forex: pd.DataFrame = yf.download(' '.join(list(depots['Forex'])), start='2021-04-01')['Close']
    forex = pd.concat([forex], keys=['Forex'], axis=1)
    forex = pd.concat([forex], keys=['Cotation'], axis=1)
    return forex


def build_metrics(assets, market, depots, forex, operation):
    df = pd.concat([market, forex], axis=1).ffill().bfill()

    for portfolio in np.unique(operation['Portfolio']):
        dfp: pd.DataFrame = operation[operation['Portfolio'] == portfolio]
        print('', portfolio)

        for asset in np.unique(dfp['Asset']):
            dfa: pd.DataFrame = dfp[dfp['Asset'] == asset]
            dfa = dfa.groupby('Date').agg({'Amount': "sum", 'Total': "sum"})
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
        else:
            df['DepositEUR', portfolio, 'All'] = 0
        df['DepositEUR', 'All', 'All'] += df['DepositEUR', portfolio, 'All']

        if 'InvestedEUR' in df.columns and portfolio in df['InvestedEUR'].columns:
            df['InvestedEUR', portfolio, 'All'] = df['InvestedEUR', portfolio].sum(axis=1)
        else:
            df['InvestedEUR', portfolio, 'All'] = 0
        df['InvestedEUR', 'All', 'All'] += df['InvestedEUR', portfolio, 'All']
        
        if 'ValueEUR' in df.columns and portfolio in df['ValueEUR'].columns:
            df['ValueEUR', portfolio, 'All'] = df['ValueEUR', portfolio].sum(axis=1)
        else:
            df['ValueEUR', portfolio, 'All'] = 0
            # df['ValueEUR', 'All', 'All'] += df['ValueEUR', portfolio, 'All']
        if 'PnLEUR' in df.columns and portfolio in df['PnLEUR'].columns:
            df['PnLEUR', portfolio, 'All'] = df['PnLEUR', portfolio].sum(axis=1)
        else:
            df['PnLEUR', portfolio, 'All'] = 0
            # df['PnLEUR', 'All', 'All'] += df['PnLEUR', portfolio, 'All']

    return df


sheets = extract_sheets()
market = fetch_market(sheets['Dicts']['assets'], sheets['Others'])
forex = fetch_forex(sheets['Dicts']['depots'])
data = build_metrics(sheets['Dicts']['assets'], market, sheets['Dicts']['depots'], forex, sheets['Operation'])


# ----------------------------------------------
# Dashboard construction
# by Streamlit
# ----------------------------------------------
st.set_page_config(layout="wide")

st.title("Portfolio Dashboard")

# ptfs = np.unique(sheets['Operation']['Portfolio'])


# with st.container():
#     cols = st.columns([1 for _ in range(len(ptfs))] + [15 - len(ptfs)])
#     for idx in range(len(ptfs)):
#         with cols[idx]:
#             display = st.checkbox(ptfs[idx])

portfo = st.radio(
    "Select a portfolio :",
    options = np.unique(sheets['Operation']['Portfolio']),
    horizontal = True
)

st.write(data[:, portfo])

tab1, tab2, tab3 = st.tabs(["Overview", "Assets", "Dataframe"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['DepositEUR', portfo, 'All'], name='Deposit'))
    fig.add_trace(go.Scatter(x=data.index, y=data['InvestedEUR', portfo, 'All'], name='Invested'))
    fig.add_trace(go.Scatter(x=data.index, y=data['ValueEUR', portfo, 'All'], name='Value'))
    fig.add_trace(go.Scatter(x=data.index, y=data['PnLEUR', portfo, 'All'], name='PnL'))
    st.plotly_chart(fig)

with tab2:
    metric = st.radio(
        "Metric to display :",
        options = ["Invested", "Value", "PnL"],
        horizontal = True
    )
    fig = go.Figure()
    for asset in data[f'{metric}EUR', portfo].columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[f'{metric}EUR', portfo, asset], name=asset))
    st.plotly_chart(fig)

with tab3:
   st.write(sheets['Operation'])


# with st.expander("Operation spreadcheet, data source"):
#     st.write(sheets['Operation'])