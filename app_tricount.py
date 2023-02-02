from typing import Dict
import warnings
import pandas as pd
import gspread as gs 
import calendar as cd
import streamlit as st
import plotly.graph_objects as go
warnings.simplefilter(action='ignore', category=pd.core.common.SettingWithCopyWarning)


@st.experimental_memo
def fetch_data():
    print("""
    # --------------------------------- #
    # Connection to Google Sheet        #
    # and extract Spreadsheets          #
    #  - exported tricount data         #
    #  - category dictonnary            #
    # --------------------------------- #
    """)
    # gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
    # ss = gc.open_by_key(st.secrets['tricount'].spreadsheet_key)
    # data = pd.DataFrame(ss.worksheet('Data').get_all_records())
    # dict = pd.DataFrame(ss.worksheet('Dict').get_all_records())
    # data.to_csv('.out/data.csv')
    # dict.to_csv('.out/dict.csv')
    data = pd.read_csv('.out/data.csv')
    dict = pd.read_csv('.out/dict.csv')
    dict2 = dict[['Postes', 'Catégories']].set_index('Catégories').to_dict()['Postes']
    print(" -- data fetched")
    print(data.shape)
    print(data.columns)
    print(" -- dict2 fetched ")
    print(dict2)
    return data, dict2


@st.experimental_memo
def build_data(data: pd.DataFrame):
    print("""
    # --------------------------------- #
    # Filter, clean and aggregate data  #
    # --------------------------------- #
    """)
    data = data[data['Catégorie'] != ""]
    data['Date'] = pd.to_datetime(data['Date & heure'], format='%d/%m/%Y %H:%M')
    data['Année'] = data['Date'].dt.year
    data['Mois'] = data['Date'].dt.month
    data['Jour'] = data['Date'].dt.day
    data['Lucie'] = data['Impacté à Lucie']
    data['Vincent'] = data['Impacté à Vincent']

    data = data.groupby(['Année', 'Mois', 'Catégorie']).sum().agg({'Lucie': "sum", 'Vincent': "sum"})
    data['Total'] = data['Lucie'] + data['Vincent']

    print(" -- data built")
    print(data.shape)
    print(data.columns)
    return data[['Total', 'Lucie', 'Vincent']]


@st.experimental_memo
def format_data(data: pd.DataFrame, dict: Dict):
    print("""
    # --------------------------------- #
    # Format and split data             #
    # by date and categories            #
    # --------------------------------- #
    """)
    tables = {}
    years = data.index.get_level_values('Année').unique().to_list()
    for year in sorted(years, reverse=True):
        df = data.loc[year,:,:]
        months = df.index.get_level_values('Mois').unique().tolist()
        tables[f'{year} (sum)'] = df.groupby('Catégorie').sum()
        tables[f'{year} (mean)'] = tables[f'{year} (sum)'] / len(months)
        for month in sorted(months, reverse=True):
            col_name = f'{year} {cd.month_name[month]}'
            tables[col_name] = df.loc[month,:].groupby('Catégorie').sum()
        # for category in set(dict.values()):
        #     if category not in tables[col_name].columns:
        #         tables[col_name][col_name] = 0
    return tables


@st.experimental_memo
def concat_data(tables: Dict[str, pd.DataFrame], dict: pd.DataFrame):
    print("""
    # --------------------------------- #
    # Build the overview result         #
    # --------------------------------- #
    """)
    result = {}
    # for table in tables.keys():
    #     tables[table]['Poste'] = dict[]
    #     result[table] = 
    return result


data, dict = fetch_data()
dframe = build_data(data)
tables = format_data(dframe)
result = concat_data(tables, dict)


print("""
    # --------------------------------- #
    # Build screen elements             #
    # --------------------------------- #
""")
# st.set_page_config(layout="wide")


st.title("Tricount Dashboard")

checks = {}
with st.sidebar:
    for table in tables.keys():
        checks[table] = st.checkbox(table)

periods = [period for period, check in checks.items() if check==True]

if len(periods) == 0:
    st.write('Tick the periods')
else:
    st.table(result[periods].style.format("{:.2f}"))

    cols = st.columns(len(periods))
    for i, col in enumerate(cols):
        with col:
            st.header(periods[i])
            st.table(tables[periods[i]].style.format("{:.2f}"))