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
import logging
# suppress warnings
import warnings
warnings.filterwarnings("ignore")

# Create and configure logger
logging.basicConfig(filename="jsoc_downloader.log",
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

# Creating an object
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_constants():
    return con.SERIES, con.SEGMENT, con.EMAIL

series, segment, email = get_constants()

def get_ar_sharp_dataframe():
    with open(os.path.join(sys.path[0], 'files', con.UPDATED_CSV_FILENAME), 'r') as csv_file:
        df = pd.read_csv(csv_file, dtype=str)
        df.dropna(subset=[con.HARP_NUMBER_COLUMN_NAME])
        return df

def extract_date_time(df, noaa):
    date_time_string = df.loc[df[con.NOAA_ACTIVE_REGION_NUMBER_COLUMN_NAME] == noaa, 'CME date and time'].iloc[0]
    need_to_strip_string = all(ele in date_time_string for ele in ["needs", "to", "be", "after"])
    if need_to_strip_string:
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
    try:
        hmi_map = sunpy.map.Map(fits_url_hmi).rotate(order=3)
    except Exception as e:
        print(f"{e}:Failed to retrieve hmi_map for {hmi_query_string}")
        hmi_map = False

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
    try:
    #resample the map to new dimensions
        rmap_resize = rmap_new.resample(new_dimensions)
    except IndexError as e:
        logger.error(f"{e}\n hmi_map: {hmi_map}\n new_dims: {new_dimensions}\n\n")
        rmap_resize = None
    yield rmap_resize

def plot_maps(hmi_map, rmap):
    #plot map
    fig = plt.figure(figsize=(18, 14))
    plt.rc("font", size=20)
    ax1 = fig.add_subplot(1, 2, 1, projection=hmi_map)
    # vmin, vmax are min and max field saturation values
    hmi_map.plot(vmin=-500, vmax=500)

    # plot resized and resmampled map
    ax2 = fig.add_subplot(1, 2, 2, projection=hmi_map)
    rmap.plot(vmin=-500, vmax=500)

    yield fig

def save_png_file(fig, noaa):
    # save figure as png file and new map to FITS file
    fig.savefig(os.path.join(sys.path[0], 'jsoc_png_files', 'AR'+noaa+'_'+t_file+'.png'))

def save_fits_file(fname, data, meta):
    # save files in fits format i.e. data and index
    sunpy.io.fits.write(os.path.join(sys.path[0], 'jsoc_fits_files', fname), data, meta, overwrite=True)


df = get_ar_sharp_dataframe()
df.dropna(subset=[con.HARP_NUMBER_COLUMN_NAME], inplace=True)
noaa_list = df[con.NOAA_ACTIVE_REGION_NUMBER_COLUMN_NAME].tolist()
print(f"Retrieved list of NOAA Active Regions with HARP NUMBERS: {len(noaa_list)} pairs\n")

while True:
    answer = input("Do you want to specify how many images to be downloaded?(y/n)\n")
    if answer.lower() == "y":
        while True:
            number_imgs = input(
                f"How many? Enter a number less than or equal to {len(noaa_list)}\n")
            try:
                number_imgs = int(number_imgs)
            except ValueError:
                continue
            if number_imgs > len(noaa_list) or number_imgs <= 0:
                continue
            else:
                noaa_list = noaa_list[:number_imgs]
                break
        break
    elif answer.lower() == "n":
        break
    else:
        print("Invalid input, use y or n\n")

for count, noaa in enumerate(noaa_list):
    sharpnum = df.loc[df[con.NOAA_ACTIVE_REGION_NUMBER_COLUMN_NAME] == noaa, con.HARP_NUMBER_COLUMN_NAME].iloc[0]
    t_str = next(extract_date_time(df, noaa))
    t_file = dt.strptime(t_str, '%Y.%m.%d_%H:%M:%S_TAI').strftime(
        '%Y%m%d_%H%M%S_TAI')
    fname = 'smap_'+noaa+t_file+'.fits'  # filename for corrected fits

    hmi_query_string = next(build_query_string(sharpnum, t_str))
    logger.info(f"Query String: {hmi_query_string}")
    hmi_map = send_jsoc_query(hmi_query_string)
    if hmi_map is None:
        continue
    else:
        rmap = next(resample_map(hmi_map, [100, 100]))
        if rmap is None:
            continue
        fig = next(plot_maps(hmi_map, rmap))
        del(hmi_map)
        save_png_file(fig, noaa)
        save_fits_file(fname, rmap.data, rmap.meta)
        print(f"Processed {count+1} / {len(noaa_list)}\n")
