import constants as con
import pandas as pd
import sunpy.map
import sunpy.io
import drms
import os
import sys
import matplotlib.pyplot as plt
from astropy import units as u
from datetime import datetime as dt
# suppress warnings
import warnings
warnings.filterwarnings("ignore")

def get_constants():
    return con.SERIES, con.SEGMENT, con.EMAIL

series, segment, email = get_constants()

def get_ar_sharp_dataframe():
    with open(os.path.join(sys.path[0], 'files', 'ARs_and_times_w_HARP_NUM.csv'), 'r') as csv_file:
        df = pd.read_csv(csv_file, dtype=str)
        df.dropna(subset=['HARP number'])
        return df

def extract_date_time(df, noaa):
    date_time_string = df.loc[df['NOAA Active region number'] == noaa, 'CME date and time'].iloc[0]
    if "needs to be after" in date_time_string:
        time, date = date_time_string.split("after")[1].split("on")
        time = time.strip()
        date = date.strip()
        combined_date_time = date+" "+time
        t_str = dt.strptime(combined_date_time,
                            '%d/%m/%Y %H:%M').strftime('%Y.%m.%d_%H:%M:00_TAI')
    else:
        date_time_string = date_time_string.strip()
        t_str = dt.strptime(date_time_string,
                            '%d/%m/%Y %H.%M.%S').strftime('%Y.%m.%d_%H:%M:00_TAI')
    yield t_str


def build_query_string(sharpnum, t_str):
    #query JSOC for magetogram file
    hmi_query_string = series+'['+str(sharpnum)+']'+'['+t_str+']'
    yield hmi_query_string


def send_jsoc_query(hmi_query_string):
    print(f"Sending query for {hmi_query_string}....")
    c = drms.Client(email=email, verbose=True)
    # Export the magnetogram as fits
    r = c.export(hmi_query_string+'{'+segment+'}', protocol='fits', email=email)
    fits_url_hmi = r.urls['url'][0]
    #create map using sunpy
    hmi_map = sunpy.map.Map(fits_url_hmi).rotate(order=3)
    if hmi_map:
        print("SUCCESS\n")
        return hmi_map
    else:
        print("FAIL\n")
        return None


def resample_map(hmi_map, new_dimensions):
    """ Take hmi magnetogram, resize to square dimensions divisible by 100
    then resample resized map to 100x100 pixels"""
    #size of data array in x and y in pixels
    x_size = int(hmi_map.data.shape[1])
    y_size = int(hmi_map.data.shape[0])

    #find minimum of x and y then find remainder when dividing by 100
    smin = min(x_size, y_size)
    srem = smin % 100
    sz = smin-srem  # reduce size by srem

    #central x,y pixels of hmi map
    xc = hmi_map.reference_pixel[1].value
    yc = hmi_map.reference_pixel[0].value

    # resize data to sz dimensions centred on xc,yc
    rmap = hmi_map.data[int(xc-sz/2):int(xc+sz/2), int(yc-sz/2):int(yc+sz/2)]
    # create a new map containing resized data
    rmap_new = sunpy.map.Map(rmap, hmi_map.meta)
    #define new dimensions to resample map, in our case this is 100x100
    new_dimensions = new_dimensions * u.pix
    #resample the map to new dimensions
    rmap_resize = rmap_new.resample(new_dimensions)
    yield rmap_resize

def plot_maps(hmi_map, rmap):
    #plot map
    fig = plt.figure(figsize=(18, 14))
    plt.rc("font", size=20)
    ax1 = fig.add_subplot(1, 2, 1)
    # vmin, vmax are min and max field saturation values
    hmi_map.plot(vmin=-500, vmax=500)

    # plot resized and resmampled map
    ax2 = fig.add_subplot(1, 2, 2)
    rmap.plot(vmin=-500, vmax=500)

    yield fig

def save_png_file(fig):
    # save figure as png file and new map to FITS file
    fig.savefig(os.path.join(sys.path[0], 'files', 'AR'+NOAA_AR+'_'+t_file+'.png'))

def save_fits_file(fname, data, meta):
    # save files in fits format i.e. data and index
    sunpy.io.fits.write(fname, data, meta)


df = get_ar_sharp_dataframe()
noaa_list = df["NOAA Active region number"].tolist()
print(f"Retrieved list of NOAA Active Regions with HARP NUMBERS: {len(noaa_list)} pairs\n")

for noaa in noaa_list[:4]:
    sharpnum = df.loc[df['NOAA Active region number'] == noaa, 'HARP number'].iloc[0]
    t_str = next(extract_date_time(df, noaa))
    t_file = dt.strptime(t_str, '%Y.%m.%d_%H:%M:%S_TAI').strftime(
        '%Y%m%d_%H%M%S_TAI')
    fname = 'smap_'+noaa+t_file+'.fits'  # filename for corrected fits

    hmi_query_string = next(build_query_string(sharpnum, t_str))
    hmi_map = send_jsoc_query(hmi_query_string)
    if hmi_map is None:
        continue
    else:
        rmap = next(resample_map(hmi_map, [100, 100]))
        fig = next(plot_maps(hmi_map, rmap))
        del(hmi_map)
        save_png_file(fig)
        save_fits_file(fname, rmap.data, rmap.meta)
