import streamlit as st
import gspread as gs 
import pandas as pd

def build_data():
    gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
    ss = gc.open_by_key(st.secrets['trading'].spreadsheet_key)
    trades = pd.DataFrame(ss.worksheet('Trades').get_all_records()).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')

    df = pd.DataFrame()
    return df