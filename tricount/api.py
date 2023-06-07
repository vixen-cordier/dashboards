from typing import Dict
import warnings
import pandas as pd
import gspread as gs 
import calendar as cd
import streamlit as st
warnings.simplefilter(action='ignore', category=pd.core.common.SettingWithCopyWarning)


def fetch_data():
    print("""
    # --------------------------------- #
    # Connection to Google Sheet        #
    # and extract Spreadsheets          #
    #  - exported tricount data         #
    #  - category dictonnary            #
    # --------------------------------- #
    """)
    gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
    ss = gc.open_by_key(st.secrets['tricount'].spreadsheet_key)
    data = pd.DataFrame(ss.worksheet('Data').get_all_records())
    dict = pd.DataFrame(ss.worksheet('Dict').get_all_records())
    # data.to_csv('.out/data.csv')
    # dict.to_csv('.out/dict.csv')
    # data = pd.read_csv('.out/data.csv')
    # dict = pd.read_csv('.out/dict.csv')
    dict = dict[['Postes', 'Catégories']].set_index('Catégories').to_dict()['Postes']
    print(" -- data fetched")
    print(data.shape)
    print(data.columns)
    print(" -- dict fetched ")
    print(dict)
    return data, dict


def build_data(data: pd.DataFrame, dict: Dict):
    print("""
    # --------------------------------- #
    # Filter, clean and aggregate data  #
    # --------------------------------- #
    """)
    data = data[data['Catégorie'] != ""]
    data['Poste'] = data['Catégorie'].apply(lambda category: dict[category])
    data['Date'] = pd.to_datetime(data['Date & heure'], format='%d/%m/%Y %H:%M')
    data['Année'] = data['Date'].dt.year
    data['Mois'] = data['Date'].dt.month
    data['Jour'] = data['Date'].dt.day
    data['Lucie'] = data['Impacté à Lucie']
    data['Vincent'] = data['Impacté à Vincent']

    brut = data.copy()[['Date', 'Titre', 'Poste', 'Catégorie', 'Payé par', 'Impacté à Lucie', 'Impacté à Vincent']]

    data = data.groupby(['Année', 'Mois', 'Poste', 'Catégorie']).agg({'Lucie': "sum", 'Vincent': "sum"})
    data['Total'] = data['Lucie'] + data['Vincent']

    print(" -- data built")
    print(data.shape)
    print(data.columns)
    return brut, data[['Total', 'Lucie', 'Vincent']]


def split_data(data: pd.DataFrame, dict: Dict):
    print("""
    # --------------------------------- #
    # Format and split data             #
    # by date and categories            #
    # --------------------------------- #
    """)
    detail: Dict[str, pd.DataFrame] = {}
    years = data.index.get_level_values('Année').unique().to_list()
    for year in sorted(years, reverse=True):
        df = data.loc[year,:,:]
        months = df.index.get_level_values('Mois').unique().tolist()
        detail[f'{year} (sum)'] = df.groupby(['Poste', 'Catégorie']).sum()
        detail[f'{year} (mean)'] = detail[f'{year} (sum)'] / len(months)

        for month in sorted(months, reverse=True):
            period = f'{year} {cd.month_name[month]}'
            detail[period] = df.loc[month,:].groupby(['Poste', 'Catégorie']).sum()

    for period in detail.keys():
        for category in set(dict.keys()):
            if (dict[category], category) not in detail[period].index:
                detail[period].loc[(dict[category], category), :] = [pd.NA, pd.NA, pd.NA]

    for period in detail.keys():
        detail[period] = detail[period].sort_index(level=['Poste', 'Catégorie'])

    return detail


def concat_data(detail: Dict[str, pd.DataFrame]):
    print("""
    # --------------------------------- #
    # Build the overview result         #
    # --------------------------------- #
    """)
    postes: Dict[str, pd.DataFrame] = {}
    result: Dict[str, pd.DataFrame] = {}
    for period in detail.keys():
        dfp = detail[period].reset_index()
        dfp = dfp.set_index('Poste')[['Total', 'Lucie', 'Vincent']]
        dfp = dfp.groupby('Poste').sum()
        postes[period] = dfp.copy()

        dfr = pd.DataFrame()
        dfp = dfp.transpose()
        dfr['Revenus'] = dfp['Rentrée d\'argent']
        dfr['Dépenses'] = dfp['Quotidien'] + dfp['Loisir'] + dfp['Extra'] + dfp['Achats']
        dfr['Reste à vivre'] = dfr['Revenus'] + dfr['Dépenses']
        dfr['Reste à vivre %'] = dfr['Reste à vivre'] / dfr['Revenus'] * 100
        dfr['Capital investi'] = - dfp['Investissement'] - dfp['Formation']
        dfr['Capital investi %'] = dfr['Capital investi'] / dfr['Revenus'] * 100
        dfr['Epargne'] = dfr['Reste à vivre'] - dfr['Capital investi']
        dfr['Epargne %'] = dfr['Epargne'] / dfr['Revenus'] * 100
        result[period] = dfr.transpose()

    return postes, result