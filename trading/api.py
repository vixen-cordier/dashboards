import streamlit as st
import gspread as gs 
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)


def fetch_data():
    print("""
    # ------------------------------------
    # Connect to Google Sheet
    # and fetch trades data
    # for Trading Dashboard 
    # ------------------------------------
    """)
    gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
    ss = gc.open_by_key(st.secrets['trading'].spreadsheet_key)
    trades = pd.DataFrame(ss.worksheet('Trades').get_values('A:AD'))
    trades = pd.DataFrame(trades.values[1:], columns=trades.iloc[0])
    trades = trades.astype({'Date': 'datetime64[ns]', 'Gain': 'float64'})
    trades = trades.sort_values('Date').reset_index(drop=True)[['Date', 'Gain', 'Result']]
    return trades


def compute_stats(df: pd.DataFrame, only_balances=False):
    trades = pd.DataFrame(index=df.index, columns=pd.MultiIndex(levels=[[],[]], codes=[[],[]]))
    trades['Date', '.'] = df['Date']

    for idx in trades.index:
        globally = 'Globally'
        yearly = f"Yearly_{df.loc[idx, 'Date'].year}"
        monthly = f"Monthly_{df.loc[idx, 'Date'].year}-{df.loc[idx, 'Date'].month}"
        weekly = f"Weekly_{df.loc[idx, 'Date'].year}-{df.loc[idx, 'Date'].week}"

        for period in [globally, yearly, monthly, weekly]:
            trades.loc[idx, ('Gain', period)] = df.loc[idx, 'Gain']
            trades.loc[idx, ('Balance', period)] = np.sum(trades.loc[:idx, ('Gain', period)])
            
            if not only_balances:
                trades.loc[idx, ('Count', period)] = trades.loc[:idx, ('Gain', period)].count()

                for result in ['SL', 'BE', 'TP']:
                    if result in df.loc[idx, 'Result']:
                        trades.loc[idx, (f'Gain{result}', period)] = trades.loc[idx, ('Gain', period)]
                        trades.loc[idx, (f'Count{result}', period)] = trades.loc[:idx, (f'Gain{result}', period)].count()
                        trades.loc[idx, (f'Rate{result}', period)] = trades.loc[idx, (f'Count{result}', period)] / trades.loc[idx, ('Count', period)]
                        trades.loc[idx, (f'Balance{result}', period)] = np.sum(trades.loc[:idx, (f'Gain{result}', period)])
                        trades.loc[idx, (f'Payoff{result}', period)] = trades.loc[idx, (f'Balance{result}', period)] / trades.loc[idx, (f'Count{result}', period)]

    return trades


def convert_to_time(df: pd.DataFrame):
    return pd.concat([
        pd.DataFrame({'Date': pd.date_range(start=df['Date'].min(), end=df['Date'].max())}).set_index('Date'),
        df.set_index('Date').groupby('Date').agg({'Gain': 'sum'}),
    ], axis=1)

