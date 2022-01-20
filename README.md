### Updating CSV file with HARP numbers

Assuming two formats:
1. There is a text file that contains pairs of data in columns with the harp number and the NOAA active region number
2. There is a csv file that has a column of NOAA active region numbers

Navigate to the root directory in your terminal and run `pipenv run python3 add_harp_numbers.py` and this will perform the operation of adding the harp numbers from the text file to the csv file if there is a match. The field will be blank if there was no match.

You can change the corresponding column names of the harp number and NOAA active region number in the csv file so that it matches (and it is important it does ) in the constants.py file.

### Downloading files from JSOC

1. Check the email, segment and series are correct in constants.py
2. Ensure there is a csv file with the harp numbers, noaa active region numbers and cme date and time existing in the folder called `files`
3. Ensure that the csv has data for the harp , noaa and date or else teh query will fail for that entry
4. Navigate to the root directory of this project in your terminal and run `pipenv run python3 jsoc_downloader.py`