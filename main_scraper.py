import requests
import os
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
from datetime import date


def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_urls(start_date, end_date):
    start_date_formatted = start_date.split("-")
    start_date_joined = "".join(start_date_formatted)
    end_date_formatted = end_date.split("-")
    end_date_joined = "".join(end_date_formatted)

    urls = []
    for year in range(int(start_date_formatted[0]), int(end_date_formatted[0])+1):
        for month in range(1, 13):
            month = "{:02}".format(month)
            for day in range(1, 32):
                day = "{:02}".format(day)
                date = int(f"{year}{month}{day}")
                if date >= int(start_date_joined) and date < int(end_date_joined) + 1:
                    urls.append(f"https://solarmonitor.org/full_disk.php?date={date}&type=shmi_maglc&region=#")

    return urls



def get_all_images(url):
    """
    Returns all image URLs on a single `url`
    """
    soup = bs(requests.get(url).content, "html.parser")

    urls = []
    for img in tqdm(soup.find_all("img"), "Extracting images"):
        img_url = img.attrs.get("src")
        if not img_url:
            # if img does not contain src attribute, just skip
            continue
            # make the URL absolute by joining domain with the URL that is just extracted
        img_url = urljoin(url, img_url)
        try:
            pos = img_url.index("?")
            img_url = img_url[:pos]
        except ValueError:
            pass
        # finally, if the url is valid
        if is_valid(img_url):
            if 'shmi_maglc_fd' in img_url:
                urls.append(img_url)
    return urls


def download(url, pathname):
    """
    Downloads a file given an URL and puts it in the folder `pathname`
    """
    # if path doesn't exist, make that path dir
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
    # download the body of response by chunk, not immediately
    response = requests.get(url, stream=True)
    # get the total file size
    file_size = int(response.headers.get("Content-Length", 0))
    # get the file name
    filename = os.path.join(pathname, url.split("/")[-1])
    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(
        1024), f"Downloading {filename}", total=file_size, unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        for data in progress.iterable:
            # write data read to the file
            f.write(data)
            # update the progress bar manually
            progress.update(len(data))


def main(path, start_date, end_date, batch_size):
    # get all urls
    urls = get_all_urls(start_date, end_date)
    imgs = []
    extracted_imgs = []
    img_counter = 0
    if len(urls) < batch_size:
        batch_size = len(urls)-1
    start = batch_size - 1
    # get all images
    for url_index in range(start, len(urls), batch_size):
        if url_index - batch_size < 0:
            start_index = 0
        else:
            start_index = url_index - batch_size
        if img_counter + (batch_size*3) > len(urls):
            urls_sliced = urls[start_index:len(urls)]
        else:
            urls_sliced = urls[start_index:url_index]
        for url in urls_sliced:
            extracted_imgs = get_all_images(url)
            imgs.extend(extracted_imgs)
        for img in imgs:
            # for each image, download it
            download(img, path)
        img_counter = img_counter + len(imgs)
        print(f"\n===================\n\nDownloaded {img_counter} images so far\n================\n")
        del imgs[0:len(imgs)]
    print(f"\n=============\nCompleted Download of {img_counter} images")


# ENTER THE START DATE HERE
default_start_date = "2011-09-11"
start_date = input(f"\nWhat is the date you wish to start at (use format YYYY-MM-DD)?\n Current start date is {default_start_date}\n")
if start_date == "":
    start_date = default_start_date

# UNCOMMENT THESE NEXT TWO LINES TO USE TODAY's DATE
# todays_date = date.today()
# end_date = todays_date.strftime("%Y-%m-%d")

# COMMENT OUT THIS LINE IF YOU WANT TO USE THE TODAY"S DATE
default_end_date = "2011-11-11"
end_date = input(
    f"\nWhat is the date you wish to end at (use format YYYY-MM-DD)?\n Current end date is {default_end_date}\n")
if end_date == "":
    end_date = default_end_date

# THIS BATCH SIZE MEANS THAT THESE NUMBER OF FILES WILL BE DOWNLOADED IN BATCHES INSTEAD OF ONE BIG BATCH. YOU CAN CHANGE THIS IF YOU'D LIKE.
default_batch_size = 5
batch_size = input(
    f"\nWhat is the batch size? i.e. The number of pictures you wish to download at a time?\n Current batch size is {default_batch_size}\n")
if batch_size == "":
    batch_size = default_batch_size

# RUNS THE PROGRAM. FIRST PARAMETER IS THE NAME OF THE FOLDER WHERE THE FILES ARE LOCATED
main("solar_monitor_magnetosphere", start_date, end_date, batch_size)
