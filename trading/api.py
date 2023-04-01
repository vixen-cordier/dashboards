import streamlit as st
import gspread as gs 
import pandas as pd

def build_data():
    gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
    ss = gc.open_by_key(st.secrets['trading'].spreadsheet_key)
    trades = pd.DataFrame(ss.worksheet('Trades').get_values('A:AD'))
    trades = pd.DataFrame(trades.values[1:], columns=trades.iloc[0])
    trades = trades.astype({'Date': 'datetime64[ns]', 'Gain': 'float64'}).sort_values('Date')
    return trades