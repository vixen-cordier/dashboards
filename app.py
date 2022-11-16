import gspread as gs 
import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go

gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
ss = gc.open_by_key(st.secrets['portfolio'].spreadsheet_key).worksheet(st.secrets['portfolio'].worksheet_name)


df = pd.DataFrame(ss.get_all_records())
df.query('Portfolio == "ZEN REMIX"', inplace=True)
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['Total']))
fig.show()

st.write(df.shape)
st.plotly_chart(fig)

