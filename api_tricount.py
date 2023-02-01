import streamlit as st
import gspread as gs 
import pandas as pd

def build_data():
    gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
    ss = gc.open_by_key(st.secrets['tricount'].spreadsheet_key)
    operation = pd.DataFrame(ss.worksheet('Data').get_all_records()[:-1])
    print(operation.shape)
    print(operation.columns)

    operation = operation[operation['Catégorie'] != ""]
    # operation = operation[operation['Type de transaction'] != "Transfert d'argent"]

    operation['Date & heure'] = pd.to_datetime(operation['Date & heure'], format='%d/%m/%Y %H:%M')
    operation['Année'] = operation['Date & heure'].dt.year
    operation['Mois'] = operation['Date & heure'].dt.month
    operation['Jour'] = operation['Date & heure'].dt.day
    operation['Lucie'] = operation['Impacté à Lucie']
    operation['Vincent'] = operation['Impacté à Vincent']

    data = operation.groupby(['Année', 'Mois', 'Catégorie']).agg({'Lucie': "sum", 'Vincent': "sum"})
    data['Total'] = data['Lucie'] + data['Vincent']

    return data[['Total', 'Lucie', 'Vincent']]
