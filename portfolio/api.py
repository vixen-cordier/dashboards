import streamlit as st
import gspread as gs 
import pandas as pd
import numpy as np
import yfinance as yf

import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)


def build_data():
    print("""
    # ----------------------------------------------
    # Get data, concate, merge and extract metrics
    # for portfolio Dashboard 
    # ----------------------------------------------
    """)

    gc = gs.service_account_from_dict(st.secrets['gcp_service_account'])
    ss = gc.open_by_key(st.secrets['portfolio'].spreadsheet_key)
    operation = pd.DataFrame(ss.worksheet('Operations').get_all_records()).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')

    dict = pd.DataFrame(ss.worksheet('Dict').get_all_records())
    assets = dict.set_index('Asset')
    print(assets)

    conf = pd.DataFrame(ss.worksheet('Conf').get_all_records())
    ext_data = pd.DataFrame()
    for (_, sheet, columns) in conf.itertuples():
        print(sheet, columns)
        ext_data = pd.concat([ext_data, pd.DataFrame(ss.worksheet(sheet).get_all_records()).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')[eval(columns)]], axis=1)

    market = yf.download(' '.join([*assets['Forex'], *assets['Download']]), start='2021-01-01')['Close']
    market = pd.concat([market, ext_data], axis=1).ffill().bfill()
    print(market.columns)   

    # operation.to_csv('.out/operation.csv')
    # assets.to_csv('.out/assets.csv')
    # market.to_csv('.out/market.csv')
    # operation = pd.read_csv('.out/operation.csv')
    # assets = pd.read_csv('.out/assets.csv')
    # market = pd.read_csv('.out/market.csv')


    df = pd.DataFrame(index=market.index, columns=pd.MultiIndex(levels=[[],[],[],[]], codes=[[],[],[],[]]))

    for portfolio in np.unique(operation['Portfolio']):
        print(portfolio)
        dfp: pd.DataFrame = operation[operation['Portfolio'] == portfolio]

        print(f"\tAssets")
        for asset in np.unique(dfp['Asset']):
            classs = assets.loc[asset]['Class']
            print(f"\t\t{classs}:\t{asset}")

            dfa: pd.DataFrame = dfp[dfp['Asset'] == asset]
            dfa = dfa.groupby('Date').agg({'Quantity': 'sum', 'Operation': 'sum'}).reindex(df.index).fillna(0)

            df[portfolio, classs, asset, 'Quantity'] = dfa['Quantity']
            df[portfolio, classs, asset, 'Operation'] = dfa['Operation']
            df[portfolio, classs, asset, 'Market'] = market[assets.loc[asset]['Market']]
            df[portfolio, classs, asset, 'Forex'] = market[assets.loc[asset]['Forex']]
        
        print(f"\tCurrency")
        for currency in np.unique(dfp['Currency']):
            classs = assets.loc[currency]['Class']
            print(f"\t\t{classs}:\t{currency}")

            dfc: pd.DataFrame = dfp[dfp['Currency'] == currency]
            dfc = dfc.groupby('Date').agg({'Quantity': 'sum', 'Operation': 'sum'}).reindex(df.index).fillna(0)
            
            if (portfolio, classs, currency, 'Quantity') not in df.columns:
                df[portfolio, classs, currency, 'Quantity'] = 0
            if (portfolio, classs, currency, 'Operation') not in df.columns:
                df[portfolio, classs, currency, 'Operation'] = 0
            if (portfolio, classs, currency, 'Market') not in df.columns:
                df[portfolio, classs, currency, 'Market'] = market[assets.loc[currency]['Market']]

            df[portfolio, classs, currency, 'Quantity'] -= dfc['Operation']
            df[portfolio, classs, currency, 'Operation'] -= dfc['Operation'] * df[portfolio, classs, currency, 'Market']


        print(f"\tBuild datatable ...")
        for asset in np.unique([*dfp['Asset'], *dfp['Currency']]):
            classs = assets.loc[asset]['Class']
            print(f"\t\t{asset}")

            toEUR = market[assets.loc[asset]['Forex']]
            df[portfolio, classs, asset, 'OperationEUR'] = df[portfolio, classs, asset, 'Operation'] / toEUR

            position, invested, investedEUR = pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)
            for idx in df.index:
                position[idx] = np.sum(df.loc[:idx][portfolio, classs, asset, 'Quantity'])
                invested[idx] = np.sum(df.loc[:idx][portfolio, classs, asset, 'Operation'])
                investedEUR[idx] = np.sum(df.loc[:idx][portfolio, classs, asset, 'OperationEUR'])

            df = pd.concat([df, pd.DataFrame({
                    (portfolio, classs, asset, 'Position'): position,
                    (portfolio, classs, asset, 'Invested'): invested,
                    (portfolio, classs, asset, 'InvestedEUR'): investedEUR,
                })], axis=1)

            df[portfolio, classs, asset, 'PRU'] = df[portfolio, classs, asset, 'Invested'] / df[portfolio, classs, asset, 'Position']
            df[portfolio, classs, asset, 'Value'] = df[portfolio, classs, asset, 'Position'] * df[portfolio, classs, asset, 'Market']
            df[portfolio, classs, asset, 'PnL'] = df[portfolio, classs, asset, 'Value'] - df[portfolio, classs, asset, 'Invested']
                
            df[portfolio, classs, asset, 'ValueEUR'] = df[portfolio, classs, asset, 'Value'] / toEUR
            df[portfolio, classs, asset, 'PnLEUR'] = df[portfolio, classs, asset, 'ValueEUR'] - df[portfolio, classs, asset, 'InvestedEUR']


        for classs in np.unique(assets['Class']):
            if classs not in df[portfolio].columns.get_level_values(0):
                df[portfolio, classs, '.', 'ValueEUR'] = 0
                df[portfolio, classs, '.', 'InvestedEUR'] = 0
                df[portfolio, classs, '.', 'PnLEUR'] = 0
                print('\t\t.', classs, 'missing')


    print(f"\t... OK")


    return df, assets