
import streamlit as st
import gspread as gs 
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

print("""
# ----------------------------------------------
# Get data, concate, merge and extract metrics
# for portfolio Dashboard 
# ----------------------------------------------
""")

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
    df['DepositEUR', 'All', 'All'] = 0
    df['InvestedEUR', 'All', 'All'] = 0
    df['ValueEUR', 'All', 'All'] = 0
    df['PnLEUR', 'All', 'All'] = 0
    df['CashEUR', 'All', 'All'] = 0

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
                    ('Amount', portfolio, asset): amt,
                    ('Invested', portfolio, asset): tot,
                })], axis=1).ffill().fillna(0)

                df['InvestedEUR', portfolio, asset] = df['Invested', portfolio, asset] * df['Cotation', 'Forex', depots['Forex'][assets['Currency'][asset]]]
                df['PRU', portfolio, asset] = df['Invested', portfolio, asset] / df['Amount', portfolio, asset]
                df['Value', portfolio, asset] = df['Amount', portfolio, asset] * df['Cotation', 'Market', assets['Market'][asset]]
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
        df['ValueEUR', 'All', 'All'] += df['ValueEUR', portfolio, 'All']

        if 'PnLEUR' in df.columns and portfolio in df['PnLEUR'].columns:
            df['PnLEUR', portfolio, 'All'] = df['PnLEUR', portfolio].sum(axis=1)
        else:
            df['PnLEUR', portfolio, 'All'] = 0
        df['PnLEUR', 'All', 'All'] += df['PnLEUR', portfolio, 'All']

        df['CashEUR', portfolio, 'All'] = df['DepositEUR', portfolio, 'All'] - df['InvestedEUR', portfolio, 'All']
        df['CashEUR', 'All', 'All'] += df['CashEUR', portfolio, 'All']

    return df


sheets = extract_sheets()
market = fetch_market(sheets['Dicts']['assets'], sheets['Others'])
forex = fetch_forex(sheets['Dicts']['depots'])
data = build_metrics(sheets['Dicts']['assets'], market, sheets['Dicts']['depots'], forex, sheets['Operation'])


print("""
# ----------------------------------------------
# Dashboard construction
# by Streamlit
# ----------------------------------------------
""")

st.set_page_config(layout="wide")

st.title("Portfolio Dashboard")
st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    font-weight: bold;
    font-size: 32px;
}
</style>
""", unsafe_allow_html=True)


all_tab, zen_tab, dma_tab = st.tabs(["Overview", "ZEN", "DMA"])

df = data[['ValueEUR', 'InvestedEUR', 'PnLEUR', 'CashEUR', 'DepositEUR']]
s = df.iloc[-1]

with all_tab:
    df_all = pd.concat({ 
        'All' : s[:, 'All', 'All'],  
        'ZEN' : s[:, 'ZEN', 'All'],  
        'DMA' : s[:, 'DMA', 'All']
    }, axis=1) 
    st.dataframe(df_all.transpose().style.format("{:.0f}"), use_container_width=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['ValueEUR', 'All', 'All'], name='Value'))
    fig.add_trace(go.Scatter(x=df.index, y=df['InvestedEUR', 'All', 'All'], name='Invested'))
    fig.add_trace(go.Scatter(x=df.index, y=df['PnLEUR', 'All', 'All'], name='PnL'))
    fig.add_trace(go.Scatter(x=df.index, y=df['CashEUR', 'All', 'All'], name='Cash'))
    fig.add_trace(go.Scatter(x=df.index, y=df['DepositEUR', 'All', 'All'], name='Deposit'))
    st.plotly_chart(fig)

    st.header("Portfolio repartition")
    pie_col, _, lin_col = st.columns([2, 1, 4])
    with pie_col:
        df_all = pd.concat({ 
            'ZEN' : df['ValueEUR', 'ZEN', 'All'],  
            'DMA' : df['ValueEUR', 'DMA', 'All'],  
            'Cash' : df['CashEUR', 'All', 'All']
        }, axis=1) 
        s_all = df_all.iloc[-1]
        fig = go.Figure(go.Pie(values=s_all.values, labels=s_all.index))
        st.plotly_chart(fig)
    
    with lin_col:
        fig = go.Figure(go.Scatter(x=df_all.index, y=df_all['ZEN'], name='ZEN', stackgroup='one', groupnorm='percent'))
        fig.add_trace(go.Scatter(x=df_all.index, y=df_all['DMA'], name='DMA', stackgroup='one'))
        fig.add_trace(go.Scatter(x=df_all.index, y=df_all['Cash'], name='Cash', stackgroup='one'))
        st.plotly_chart(fig)


    st.header("Portfolio performance")
    df_all = pd.concat({ 
        'ZEN' : df['PnLEUR', 'ZEN', 'All'],  
        'DMA' : df['PnLEUR', 'DMA', 'All'],  
        'All' : df['PnLEUR', 'All', 'All']
    }, axis=1) 
    s_all = df_all.iloc[-1]
    fig = go.Figure(go.Bar(x=s_all.index, y=s_all.values))
    st.plotly_chart(fig)



def datatable_ptf(s, ptf):
    rows = {}
    rows['All'] = s[:, ptf, 'All']
    for asset in s['ValueEUR', ptf].index:
        if asset != 'All':
            rows[asset] = s[:, ptf, asset]
    table = pd.concat(rows, axis=1) 
    st.dataframe(table.transpose().style.format("{:.0f}"), use_container_width=True)

def scatter_ptf(df, ptf):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['ValueEUR', ptf, 'All'], name='Value'))
    fig.add_trace(go.Scatter(x=df.index, y=df['InvestedEUR', ptf, 'All'], name='Invested'))
    fig.add_trace(go.Scatter(x=df.index, y=df['PnLEUR', ptf, 'All'], name='PnL'))
    fig.add_trace(go.Scatter(x=df.index, y=df['CashEUR', ptf, 'All'], name='Cash'))
    fig.add_trace(go.Scatter(x=df.index, y=df['DepositEUR', ptf, 'All'], name='Deposit'))
    st.plotly_chart(fig)

def scatter_metric(df, ptf, metric):
    fig = go.Figure()
    for asset in df[metric, ptf].columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[metric, ptf, asset], name=asset))
    st.plotly_chart(fig)

def pie_metric(s, ptf, metric):
    value = []
    label = []
    for asset in s[metric, ptf].index:
        if asset != 'All':
            value.append(s[metric, ptf, asset])
            label.append(asset)
    fig = go.Figure(go.Pie(values=value, labels=label))
    st.plotly_chart(fig)

def stack_metric(df, ptf, metric):
    fig = go.Figure()
    for asset in df[metric, ptf].columns:
        if asset != 'All':
            fig.add_trace(go.Scatter(x=df.index, y=df[metric, ptf, asset], name=asset, stackgroup='one', groupnorm='percent'))
    st.plotly_chart(fig)

def bar_metric(s, ptf, metric):
    value = []
    label = []
    for asset in s[metric, ptf].index:
        value.append(s[metric, ptf, asset])
        label.append(asset)
    fig = go.Figure(go.Bar(x=label, y=value))
    st.plotly_chart(fig)


with zen_tab:
    datatable_ptf(s, 'ZEN')
    scatter_ptf(df, 'ZEN')

    st.header("ZEN Value")
    scatter_metric(df, 'ZEN', 'ValueEUR')

    pie_col, lin_col = st.columns([1, 2])
    with pie_col:
        pie_metric(s, 'ZEN', 'ValueEUR')

    with lin_col:
        stack_metric(df, 'ZEN', 'ValueEUR')

    st.header("ZEN Performance")
    bar_metric(s, 'ZEN', 'PnLEUR')



# with st.expander("Operation spreadcheet, data source"):
#     st.write(sheets['Operation'])
# with st.expander("df"):
#     st.write(data.loc[:, pd.IndexSlice[:, ['Forex', 'ZEN'], 'All']])