#!/usr/bin/env python
# coding: utf-8
"""
Created on Thu Aug 12 14:33:21 2021

Find HARP number of AR
Download, read and plot SHARP magnetogram data
Resize and resample map
Save as a new FITS file

@author: stephanieyardley

"""

#import required python/SunPy packages
from __future__ import division, print_function
import os.path
import matplotlib.pyplot as plt
import drms
import datetime
import sunpy.map
from astropy import units as u
import sunpy.io

# suppress warnings
import warnings
warnings.filterwarnings("ignore")

# Define working directory
wdir = '/Users/nadiakhan/desktop/THESIS 2021/'

# NOAA AR number and time of magnetogram
# Note that magnetograms have a cadence of 12 minutes
# so available at 00,12,24,36,48 but JSOC will find
# nearest available magnetogram to t_file time
# TODO Are these NOAA numbers coming from the csv filr. This is the first column
NOAA_AR = '11374'
# TODO: What is the file here? The first string before the underscore is the date related to the active region. Nothing else changes
t_file = '20111214_205800_TAI'
t_str = datetime.datetime.strptime(t_file, '%Y%m%d_%H%M%S_TAI').strftime('%Y.%m.%d_%H:%M:%S_TAI')

#we want to use the SHARPS CEA series
series = 'hmi.sharp_cea_720s'
# we want magnetorgrams
segment = 'magnetogram'

#TODO: What is this file check for? What is it returning. The Sharpnum but in the file there are none
def check_file(filename, string):
    """ Check if any line in the file contains given string """
    # Open the file in read only mode
    with open(filename, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if string in line:
                return int(line.strip().split()[0])
    return False


def resample_map(hmi_map, new_dimensions):
    """ Take hmi magnetogram, resize to square dimensions divisible by 100
    then resample resized map to 100x100 pixels"""
    #size of data array in x and y in pixels
    x_size = int(hmi_map.data.shape[1])
    y_size = int(hmi_map.data.shape[0])

    #find minimum of x and y then find remainder when dividing by 100
    smin = min(x_size, y_size)
    srem = smin % 100
    sz = smin-srem # reduce size by srem

    #central x,y pixels of hmi map
    xc = hmi_map.reference_pixel[1].value
    yc = hmi_map.reference_pixel[0].value

    # resize data to sz dimensions centred on xc,yc
    rmap = hmi_map.data[int(xc-sz/2):int(xc+sz/2),int(yc-sz/2):int(yc+sz/2)]
    # create a new map containing resized data
    rmap_new = sunpy.map.Map(rmap, hmi_map.meta)
    #define new dimensions to resample map, in our case this is 100x100
    new_dimensions = new_dimensions * u.pix
    #resample the map to new dimensions
    rmap_resize = rmap_new.resample(new_dimensions)
    return rmap_resize


# check the harps txt file for NOAA AR number and return HARPS number
# using check_file function defined above
sharpnum = check_file('all_harps_with_noaa_ars.txt', NOAA_AR)
# print HARP number
print(sharpnum)

# TODO: What is the email here for? Do i need it to access JSOC? Should i keep using your mail?
# email address - please change
email = 'nadia.khan.19@ucl.ac.uk'

#magnetogram file
hmi_file = series+'.'+str(sharpnum)+'.'+t_file+'.'+segment+'.fits'

# name for resulting fits file
fname = 'smap_'+NOAA_AR+t_file+'.fits' #filename for corrected fits

if not os.path.exists(fname):

    #query JSOC for magetogram file
    hmi_query_string = series+'['+str(sharpnum)+']'+'['+t_str+']'

    c = drms.Client(email=email, verbose=True)
    # Export the magnetogram as fits
    r = c.export(hmi_query_string+'{'+segment+'}', protocol='fits', email=email)
    #dl = r.download(',') #include this if you want to download the file
    fits_url_hmi = r.urls['url'][0]

    #create map using sunpy
    hmi_map = sunpy.map.Map(fits_url_hmi).rotate(order=3)
    # create resampled map
    rmap = resample_map(hmi_map, [100,100])

    #plot map
    fig = plt.figure(figsize=(18,14))
    plt.rc("font", size=20)
    ax1 = fig.add_subplot(1,2,1)
    hmi_map.plot(vmin=-500,vmax=500) #vmin, vmax are min and max field saturation values

    # plot resized and resmampled map
    ax2 = fig.add_subplot(1,2,2)
    rmap.plot(vmin=-500,vmax=500)

    # save figure as png file and new map to FITS file
    fig.savefig('AR'+NOAA_AR+'_'+t_file+'.png')
    sunpy.io.fits.write(fname, rmap.data, rmap.meta) #save files in fits format i.e. data and index

    # print file name
    print(fname)
