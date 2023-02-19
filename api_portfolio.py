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
    dicts = pd.DataFrame(ss.worksheet('Dict').get_all_records())
    operation = pd.DataFrame(ss.worksheet('Operations').get_all_records()).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')
    greenbull = pd.DataFrame(ss.worksheet('GREENBULL').get_all_records()).sort_values('Date').astype({'Date': 'datetime64[ns]'}).set_index('Date')
    assets = dicts.set_index('Asset')
    print(assets, '\n')

    market = yf.download(' '.join(list(assets['Forex'])+list(assets['Market'])[:-1]), start='2021-04-01')['Close']
    market = pd.concat([market, greenbull], axis=1).ffill().bfill()
    print(market.columns)

    # market = pd.concat([market], keys=['Market'], axis=1)
    # market = pd.concat([market], keys=['Cotation'], axis=1)

    # operation.to_csv('.out/operation.csv')
    # assets.to_csv('.out/assets.csv')
    # market.to_csv('.out/market.csv')
    # operation = pd.read_csv('.out/operation.csv')
    # assets = pd.read_csv('.out/assets.csv')
    # market = pd.read_csv('.out/market.csv')

    df = market
    # print(df.head())

    for portfolio in np.unique(operation['Portfolio']):
        print(portfolio)
        dfp: pd.DataFrame = operation[operation['Portfolio'] == portfolio]

        print(f"\tAssets")
        for asset in np.unique(dfp['Asset']):
            print(f"\t\t{assets.loc[asset]['Class']}:\t{asset}")

            dfa: pd.DataFrame = dfp[dfp['Asset'] == asset]
            dfa = dfa.groupby('Date').agg({'Quantity': "sum", 'Total': "sum"}).reindex(df.index).fillna(0)

            df['Quantity', portfolio, asset] = dfa['Quantity']
            df['Total', portfolio, asset] = dfa['Total']
        
        print(f"\tCurrency")
        for currency in np.unique(dfp['Currency']):
            print(f"\t\t{assets.loc[currency]['Class']}:\t{currency}")

            dfc: pd.DataFrame = dfp[dfp['Currency'] == currency]
            dfc = dfc.groupby('Date').agg({'Quantity': "sum", 'Total': "sum"}).reindex(df.index).fillna(0)
            
            if ('Quantity', portfolio, currency) not in df.columns:
                df['Quantity', portfolio, currency] = 0
            if ('Total', portfolio, currency) not in df.columns:
                df['Total', portfolio, currency] = 0

            df['Quantity', portfolio, currency] -= dfc['Total']
            df['Total', portfolio, currency] -= dfc['Total'] * df['Cotation', 'Market', assets.loc[currency]['Market']]


        print(f"Build datatable ...")
        for asset in np.unique([*dfp['Asset'], *dfp['Currency']]):
            print("\t", asset)

            amount, invest = pd.Series(dtype=float), pd.Series(dtype=float)
            for idx in df.index:
                amount[idx] = np.sum(df.loc[:idx]['Quantity', portfolio, asset])
                invest[idx] = np.sum(df.loc[:idx]['Total', portfolio, asset])

            df = pd.concat([df, pd.DataFrame({
                    ('Amount', portfolio, asset): amount,
                    ('Invested', portfolio, asset): invest,
                })], axis=1)

            df['Cotation', portfolio, asset] = df['Cotation', 'Market', assets.loc[asset]['Market']]
            df['Class', portfolio, asset] = assets.loc[asset]['Class']
            df['PriceFmt', portfolio, asset] = assets.loc[asset]['PriceFmt']
            df['ValueFmt', portfolio, asset] = assets.loc[asset]['ValueFmt']
            df['AmountFmt', portfolio, asset] = assets.loc[asset]['AmountFmt']

            if assets.loc[asset]['Class'] == 'Deposit':
                df['Deposited', portfolio, asset] = -df['Invested', portfolio, asset]
                df['DepositedEUR', portfolio, asset] = df['Deposited', portfolio, asset]
            
            else:
                df['PRU', portfolio, asset] = df['Invested', portfolio, asset] / df['Amount', portfolio, asset]
                df['Value', portfolio, asset] = df['Amount', portfolio, asset] * df['Cotation', portfolio, asset]
                df['PnL', portfolio, asset] = df['Value', portfolio, asset] - df['Invested', portfolio, asset]
                
                toEUR = df['Cotation', 'Market', assets.loc[asset]['Forex']]
                df['InvestedEUR', portfolio, asset] = df['Invested', portfolio, asset] / toEUR
                df['ValueEUR', portfolio, asset] = df['Value', portfolio, asset] / toEUR
                df['PnLEUR', portfolio, asset] = df['PnL', portfolio, asset] / toEUR


        print(f"Concate data ...")
        df['DepositedEUR', portfolio, 'All'] = df.loc[:, pd.IndexSlice['DepositedEUR', portfolio, :]].sum(axis=1)
        df['InvestedEUR', portfolio, 'All'] = df.loc[:, pd.IndexSlice['InvestedEUR', portfolio, :]].sum(axis=1) - df['DepositedEUR', portfolio, 'All']
        df['ValueEUR', portfolio, 'All'] = df.loc[:, pd.IndexSlice['ValueEUR', portfolio, :]].sum(axis=1)
        df['PnLEUR', portfolio, 'All'] = df.loc[:, pd.IndexSlice['PnLEUR', portfolio, :]].sum(axis=1)
        df['CashEUR', portfolio, 'All'] = df['DepositedEUR', portfolio, 'All'] - df['InvestedEUR', portfolio, 'All']

    df['DepositedEUR', 'All', 'All'] = df.loc[:, pd.IndexSlice['DepositedEUR', :, 'All']].sum(axis=1)
    df['InvestedEUR', 'All', 'All'] = df.loc[:, pd.IndexSlice['InvestedEUR', :, 'All']].sum(axis=1)
    df['ValueEUR', 'All', 'All'] = df.loc[:, pd.IndexSlice['ValueEUR', :, 'All']].sum(axis=1)
    df['PnLEUR', 'All', 'All'] = df.loc[:, pd.IndexSlice['PnLEUR', :, 'All']].sum(axis=1)
    df['CashEUR', 'All', 'All'] = df.loc[:, pd.IndexSlice['CashEUR', :, 'All']].sum(axis=1)
    
    return df