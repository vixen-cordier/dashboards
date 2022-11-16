import gspread as gs
import pandas as pd

key = 

gc = gs.service_account(filename='cred-api-sheets.json')

ss_portfolio_key = '1xhq1RGQLcuUVr88-5Gl4tEvY0eI5M_i8TkkzRZwSC80'
ss_portfolio = gc.open_by_key(ss_portfolio_key).worksheet("Operations")
df_portfolio = pd.DataFrame(ss_portfolio.get_all_records())
df_portfolio