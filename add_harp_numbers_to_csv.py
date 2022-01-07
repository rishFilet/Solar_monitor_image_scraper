import sys
import os
import pandas as pd

def add_harp_numbers():
    with open(os.path.join(sys.path[0], 'files', 'all_harps_with_noaa_ars.txt'), 'r') as txt_file:
        txt_df = pd.read_csv(txt_file, sep=" ", dtype=str)
        txt_df.columns = ['HARP number', 'NOAA Active region number']

    with open(os.path.join(sys.path[0], 'files', 'ARs_and_times.csv'), 'r') as csv_file:
        csv_df = pd.read_csv(csv_file, dtype=str)
        csv_df.columns = csv_df.columns.str.strip()
        csv_df.drop('HARP number', axis=1, inplace=True)
        merged_df = pd.merge(csv_df, txt_df, how="left", on=["NOAA Active region number"])

    merged_df.to_csv(os.path.join(sys.path[0], 'files', 'ARs_and_times_w_HARP_NUM.csv'))

add_harp_numbers()
