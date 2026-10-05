import numpy as np
import requests
import sqlite3
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks"
db_name = 'Banks.db'
table_name = 'Largest_banks'
csv_path = 'Largest_banks_data.csv'
log_file = 'code_log.txt'

def log_progress(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, "a") as f:
        f.write(f"{timestamp} : {message}\n")

def extract(url, table_attribs):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    rows = soup.find_all("tbody")[0].find_all("tr")
    for row in rows:
        columns = row.find_all('td')
        if len(columns) >= 3:
            rank = columns[0].get_text(strip=True)
            bank_name = columns[1].get_text(strip=True)
            market_cap_text = columns[2].get_text()
            market_cap = float(market_cap_text[:-1].strip().replace(",", ""))
            data = {
                "Rank": rank,
                "Bank_name": bank_name,
                "MC_USD_Billion": market_cap
            }
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    return df

def transform(df, csv_path):
    exchange_rate_df = pd.read_csv(csv_path)
    exchange_rate = exchange_rate_df.set_index(
        exchange_rate_df.columns[0]
    ).to_dict()[exchange_rate_df.columns[1]]

    gbp_rate = float(exchange_rate["GBP"])
    eur_rate = float(exchange_rate["EUR"])
    inr_rate = float(exchange_rate["INR"])

    df["MC_GBP_Billion"] = [np.round(v * gbp_rate, 2) for v in df["MC_USD_Billion"]]
    df["MC_EUR_Billion"] = [np.round(v * eur_rate, 2) for v in df["MC_USD_Billion"]]
    df["MC_INR_Billion"] = [np.round(v * inr_rate, 2) for v in df["MC_USD_Billion"]]

    return df

def load_to_csv(df, output_path):
    df.to_csv(output_path, index=False)

def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists="replace", index=False)

def run_query(query_statement, sql_connection):
    query_output = pd.read_sql_query(query_statement, sql_connection)
    print(query_output)

# --- Main execution ---
exchange_rate_csv = "exchange_rate.csv"
output_csv = "Largest_banks_data.csv"

table_attribs = ["Rank", "Bank_name", "MC_USD_Billion"]

log_progress("Preliminaries complete. Initiating extraction process.")
df = extract(url, table_attribs)
log_progress("Data extraction complete. Initiating transformation process.")
df = transform(df, exchange_rate_csv)
print(df)
log_progress("Data transformation complete. Initiating CSV loading.")
load_to_csv(df, output_csv)
log_progress("Data loaded to CSV file.")

sql_connection = sqlite3.connect(db_name)
load_to_db(df, sql_connection, table_name)
log_progress("Data loaded to database.")

query_statement = f"SELECT * FROM {table_name}"
run_query(query_statement, sql_connection)
sql_connection.close()
log_progress("Process complete.")   

