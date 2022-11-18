import streamlit as st
import gspread as gs

gc = gs.service_account(filename=st.secrets["gcp_service_account"])
ss_portfolio_key = '1xhq1RGQLcuUVr88-5Gl4tEvY0eI5M_i8TkkzRZwSC80'
ss_portfolio = gc.open_by_key(ss_portfolio_key).worksheet("Operations")

# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)

# Perform SQL query on the Google Sheet.
# Uses st.cache to only rerun when the query changes or after 10 min.
@st.cache(ttl=600)
def run_query(query):
    rows = conn.execute(query, headers=1)
    rows = rows.fetchall()
    return rows

sheet_url = st.secrets["private_gsheets_url"]
rows = run_query(f'SELECT * FROM "{sheet_url}"')

# Print results.
for row in rows:
    st.write(f"{row.name} has a :{row.pet}:")