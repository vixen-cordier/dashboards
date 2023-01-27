import streamlit as st
import gspread as gs 
import pandas as pd

gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
ss = gc.open_by_key(st.secrets['quotidien'].spreadsheet_key)
operation = pd.DataFrame(ss.worksheet('Data').get_all_records()[:-1])
print(operation.shape)
print(operation.columns)

operation['Date & heure'] = pd.to_datetime(operation['Date & heure'], format='%d/%m/%Y %H:%M')
operation['Ann�e'] = operation['Date & heure'].dt.year
operation['Mois'] = operation['Date & heure'].dt.month
operation['Jour'] = operation['Date & heure'].dt.day

df = operation.groupby(['Ann�e', 'Mois', 'Cat�gorie']).agg({'Impact� � Lucie': "sum", 'Impact� � Vincent': "sum"})
