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
    assets = dicts[['Asset', 'Market', 'Currency', 'Forex', 'IsDepot']].set_index('Asset')
    # depots = dicts[['Depot', 'Forex']].set_index('Depot')
    print(assets, '\n')
    # print(depots)

    market = yf.download(' '.join(list(assets['Forex'])+list(assets['Market'])[:-1]), start='2021-04-01')['Close']
    market = pd.concat([market, greenbull], axis=1)
    market = pd.concat([market], keys=['Market'], axis=1)
    market = pd.concat([market], keys=['Cotation'], axis=1)

    # forex: pd.DataFrame = yf.download(' '.join(list(depots['Forex'])), start='2021-04-01')['Close']
    # forex = pd.concat([forex], keys=['Forex'], axis=1)
    # forex = pd.concat([forex], keys=['Cotation'], axis=1)


    # df = pd.concat([market, forex], axis=1).ffill().bfill()
    df = market.ffill().bfill()
    df['DepositEUR', 'All', 'All'] = 0
    df['InvestedEUR', 'All', 'All'] = 0
    df['ValueEUR', 'All', 'All'] = 0
    df['PnLEUR', 'All', 'All'] = 0
    df['CashEUR', 'All', 'All'] = 0

    for portfolio in np.unique(operation['Portfolio']):
        dfp: pd.DataFrame = operation[operation['Portfolio'] == portfolio]
        print(portfolio)

        for asset in np.unique(dfp['Asset']):
            dfa: pd.DataFrame = dfp[dfp['Asset'] == asset]
            dfa = dfa.groupby('Date').agg({'Amount': "sum", 'Total': "sum"})

            amt, tot = pd.Series(dtype=float), pd.Series(dtype=float)
            for idx in dfa.index:
                amt[idx] = np.sum(dfa.loc[:idx]['Amount'])
                tot[idx] = np.sum(dfa.loc[:idx]['Total'])

            if assets.loc[asset]['IsDepot'] == 'TRUE':
                df = pd.concat([df, pd.DataFrame({
                    ('Amount', portfolio, asset): amt,
                    ('Deposit', portfolio, asset): tot,
                })], axis=1).ffill().fillna(0)

                print(f"\tdepot:  {asset}")
                df['DepositEUR', portfolio, asset] = df['Deposit', portfolio, asset] * df['Cotation', 'Market', assets.loc[asset]['Forex']]
                # df['PnL', portfolio, asset] = df['Deposit', portfolio, asset] - df['DepositEUR', portfolio, asset]
                # df['PnLEUR', portfolio, asset] = df['PnL', portfolio, asset] * df['Cotation', 'Forex', depots['Forex'][asset]]

                df['Cotation', portfolio, asset] = df['Cotation', 'Market', assets.loc[asset]['Market']]
                df['Currency', portfolio, asset] = assets.loc[asset]['Currency']

            else:
                df = pd.concat([df, pd.DataFrame({
                    ('Amount', portfolio, asset): amt,
                    ('Invested', portfolio, asset): tot,
                })], axis=1).ffill().fillna(0)

                print(f"\tasset:  {asset}")
                df['InvestedEUR', portfolio, asset] = df['Invested', portfolio, asset] / df['Cotation', 'Market', assets.loc[asset]['Forex']]
                df['PRU', portfolio, asset] = df['Invested', portfolio, asset] / df['Amount', portfolio, asset]
                df['Value', portfolio, asset] = df['Amount', portfolio, asset] * df['Cotation', 'Market', assets.loc[asset]['Market']]
                df['ValueEUR', portfolio, asset] = df['Value', portfolio, asset] / df['Cotation', 'Market', assets.loc[asset]['Forex']]
                df['PnL', portfolio, asset] = df['Value', portfolio, asset] - df['Invested', portfolio, asset]
                df['PnLEUR', portfolio, asset] = df['PnL', portfolio, asset] / df['Cotation', 'Market', assets.loc[asset]['Forex']]

                df['Cotation', portfolio, asset] = df['Cotation', 'Market', assets.loc[asset]['Market']]
                df['Currency', portfolio, asset] = assets.loc[asset]['Currency']


        if 'DepositEUR' in df.columns and portfolio in df['DepositEUR'].columns:
            df['DepositEUR', portfolio, 'All'] = df['DepositEUR', portfolio].sum(axis=1)
        else:
            df['DepositEUR', portfolio, 'All'] = 0
        df['DepositEUR', 'All', 'All'] += df['DepositEUR', portfolio, 'All']

        if 'InvestedEUR' in df.columns and portfolio in df['InvestedEUR'].columns:
            df['InvestedEUR', portfolio, 'All'] = df['InvestedEUR', portfolio].sum(axis=1)
        else:
            df['InvestedEUR', portfolio, 'All'] = 0
        df['InvestedEUR', 'All', 'All'] += df['InvestedEUR', portfolio, 'All']
        
        if 'ValueEUR' in df.columns and portfolio in df['ValueEUR'].columns:
            df['ValueEUR', portfolio, 'All'] = df['ValueEUR', portfolio].sum(axis=1)
        else:
            df['ValueEUR', portfolio, 'All'] = 0
        df['ValueEUR', 'All', 'All'] += df['ValueEUR', portfolio, 'All']

        if 'PnLEUR' in df.columns and portfolio in df['PnLEUR'].columns:
            df['PnLEUR', portfolio, 'All'] = df['PnLEUR', portfolio].sum(axis=1)
        else:
            df['PnLEUR', portfolio, 'All'] = 0
        df['PnLEUR', 'All', 'All'] += df['PnLEUR', portfolio, 'All']

        df['CashEUR', portfolio, 'All'] = df['DepositEUR', portfolio, 'All'] - df['InvestedEUR', portfolio, 'All']
        df['CashEUR', 'All', 'All'] += df['CashEUR', portfolio, 'All']
    
    return df