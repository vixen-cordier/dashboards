import gspread as gs
import pandas as pd

gc = gs.service_account(filename='cred-api-sheets.json')

ss_trading_key = '10hUsIQ-80eaS_ooJJ2_2XAaD45LINXLkzVm7FAF4UNY'
ss_trading = gc.open_by_key(ss_trading_key).worksheet("Trades")
df_trading = pd.DataFrame(ss_trading.get_all_records())
df_trading