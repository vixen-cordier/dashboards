import streamlit as st
import gspread as gs 
import pandas as pd
import numpy as np
import datetime as dt
import yfinance as yf
import plotly.graph_objects as go

## Connect to Google Sheet
gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
ss_portfolio = gc.open_by_key(st.secrets['portfolio'].spreadsheet_key).worksheet(st.secrets['portfolio'].worksheet_name)

## Get data from Spreadsheet
df_portfolio = pd.DataFrame(ss_portfolio.get_all_records())
# Rework data
eurusd: pd.DataFrame = yf.download('EURUSD=X', start=min(df_portfolio['Date']))[['Close']]
df_portfolio['EURUSD'] = [eurusd[eurusd.index == df_portfolio.loc[idx]['Date']]['Close'].values[0] for idx in df_portfolio.index]
df_portfolio['Total€'] = [df_portfolio.loc[idx]['Total'] / (1 if df_portfolio.loc[idx]['Currency'] == "€" else df_portfolio.loc[idx]['EURUSD']) for idx in df_portfolio.index]

## Create sub dataframe to filter data
# All Deposit
df_deposit = df_portfolio[(df_portfolio['Portfolio'] == "ZEN REMIX") & (df_portfolio['Asset'].str.contains("Deposit"))]
df_deposit = df_deposit.groupby('Date').agg({'Total€': "sum"})
df_deposit['Deposit€'] = [np.sum(df_deposit.loc[:idx]['Total€']) for idx in df_deposit.index]
# All investment
df_invested = df_portfolio[(df_portfolio['Portfolio'] == "ZEN REMIX") & (~df_portfolio['Asset'].str.contains("Deposit"))]
df_invested = df_invested.groupby('Date').agg({'Total€': "sum"})
df_invested['Invested€'] = [np.sum(df_invested.loc[:idx]['Total€']) for idx in df_invested.index]

## Build dataframe to display it
df = pd.DataFrame({'Date': pd.date_range(start=min(df_portfolio['Date']), end=dt.datetime.now())})
df = df.merge(df_invested.reset_index()[['Date', 'Invested€']].astype({'Date': 'datetime64[ns]', 'Invested€': 'int64'}), on='Date', how='left').ffill()
df = df.merge(df_deposit.reset_index()[['Date', 'Deposit€']].astype({'Date': 'datetime64[ns]', 'Deposit€': 'int64'}), on='Date', how='left').ffill()

## Streamlit elements
# st.write(df_portfolio)
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['Deposit€']))
fig.add_trace(go.Scatter(x=df['Date'], y=df['Invested€']))
st.plotly_chart(fig)

with st.expander("Source dataframe"):
    st.write(df_portfolio)