import sys
import os
import pandas as pd
import constants as con

def add_harp_numbers():
    with open(os.path.join(sys.path[0], 'files', con.TXT_FILENAME), 'r') as txt_file:
        txt_df = pd.read_csv(txt_file, sep=" ", dtype=str)
        txt_df.columns = [con.HARP_NUMBER_COLUMN_NAME, con.NOAA_ACTIVE_REGION_NUMBER_COLUMN_NAME]

    with open(os.path.join(sys.path[0], 'files', con.ORIGINAL_CSV_FILENAME), 'r') as csv_file:
        csv_df = pd.read_csv(csv_file, dtype=str)
        csv_df.columns = csv_df.columns.str.strip()
        csv_df.drop(con.HARP_NUMBER_COLUMN_NAME, axis=1, inplace=True)
        merged_df = pd.merge(csv_df, txt_df, how="left", on=[con.NOAA_ACTIVE_REGION_NUMBER_COLUMN_NAME])

    merged_df.to_csv(os.path.join(sys.path[0], 'files', con.UPDATED_CSV_FILENAME))

add_harp_numbers()
