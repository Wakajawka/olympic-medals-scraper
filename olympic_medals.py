import numpy as np
import requests
import sqlite3
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import io

url = "https://en.wikipedia.org/wiki/All-time_Olympic_Games_medal_table"
db_name = 'medals.db'
table_name = 'all_time_olympic_medals'
csv_path = 'olympic_medals.csv'
log_file = 'code_log.txt'

def log_progress(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, "a") as f:
        f.write(f"{timestamp} : {message}\n")
def safe_int(val):
    val = val.replace(',', '').replace('†', '').replace('*', '').strip()
    try:
        return int(val)
    except ValueError:
        return 0

def extract(url, table_attribs):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    page = requests.get(url, headers=headers).text

    tables = pd.read_html(io.StringIO(page))
    df = None
    for t in tables:
        cols = [str(c).strip() for c in t.columns]
        if 'NOC' in cols and 'Gold' in cols and 'Total' in cols:
            if df is None or len(t) > len(df):
                df = t   

    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Rank': 'No.', 'NOC': 'Nation'})   
    df = df[table_attribs]
    df['Nation'] = df['Nation'].str.replace(r'\*|\[.*?\]', '', regex=True).str.strip()   

    for col in ['Gold', 'Silver', 'Bronze', 'Total']:
        df[col] = df[col].astype(str).str.replace(r'[^\d]', '', regex=True).astype(int)

    return df    
def load_to_csv(df, output_path):
    df.to_csv(output_path, index=False)

def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists="replace", index=False)

def run_query(query_statement, sql_connection):
    query_output = pd.read_sql_query(query_statement, sql_connection)
    print("=== TOP 20 ===")
    print(query_output.to_string(index=False))    
   
table_attribs = ["No.", "Nation", "Gold", "Silver", "Bronze", "Total"]
log_progress("Preliminaries complete. Initiating extraction process.")
df = extract(url, table_attribs)
log_progress("Data extraction complete. Loading to csv.")
df = df.reset_index(drop=True)
load_to_csv(df,csv_path)
log_progress('Loading to csv complete. Loading to db.')
sql_connection = sqlite3.connect(db_name)
load_to_db(df, sql_connection, table_name)
log_progress("Data loaded to database.")
log_progress('Data succesfully loaded to db.')
query_statement = f"SELECT * FROM {table_name} LIMIT 30"   
print(f"Total rows in df: {len(df)}")   
run_query(query_statement, sql_connection)
sql_connection.close()
log_progress("Process complete.")   

