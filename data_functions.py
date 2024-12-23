# built in libraries
import csv
from datetime import datetime
import json
import os
import re
import requests

# third party libraries
import pandas as pd
import usaddress
from usaddress import RepeatedLabelError
from nameparser import HumanName


def remove_tabs(x):
    if isinstance(x, str):
        # Replace tabs with spaces, remove multiple spaces, and strip leading/trailing whitespace
        return ' '.join(x.replace('\t', ' ').split()).strip()
    return x

# consumer A2.1 values
def reformat_consumer_names(value):
    if not isinstance(value, str):
        return value
    name = HumanName(value)
    formatted_name = f"{name.last}, {name.suffix} {name.title} {name.first} {name.middle}"
    # remove extra spaces in formatted name
    formatted_name = re.sub(r'\s+', ' ', formatted_name).strip()
    return formatted_name

# commercial A2.1 values 
def reformat_commercial_names(value):
    if not isinstance(value, str):
        return value
    value = re.sub(r'[,.]', '', value)
    return value

# used by Matheson function (apply to all)
def reformat_commercial_values(value):
    if not isinstance(value, str):
        return value
    value = value.replace("'", "")
    value = re.sub('[^a-zA-Z&]', ' ', value)

    return value

def format_zipcode(zipcode):
    try:
        zipcode = str(int(float(zipcode)))
        if len(zipcode) > 5 and '-' not in zipcode:
            return f"{zipcode[:5]}-{zipcode[5:]}"
        if len(zipcode) < 5:
            zipcode = zipcode.zfill(5)
    except Exception as e:
        pass

    return zipcode


# automate file path finding given parent folder 
# return list of excel file paths given folder path
# REMOVE replace with parse_excel_files()
def excel_files_to_list(parent_folder_name):
    file_paths = []
    for root, dirs, files in os.walk(parent_folder_name):
        for file_name in files:
            if file_name.endswith(('.xls', '.xlsx')):
                file_path = os.path.join(root, file_name)
                file_paths.append(file_path)
    return file_paths

# formats the numerical (money) amount to 2 decimal places
def format_amount(value):
    try:
           
        if pd.isna(value):
            return ""

        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return value

def parse_excel_files(file_path):
    """
    Parses all Excel files in the given directory and converts each sheet to a CSV file.
    Args:
        file_path (str): The directory path containing the Excel files to be parsed.
    Returns:
        None
    This function iterates through all files in the specified directory, identifies files with
    '.xls' or '.xlsx' extensions, and reads each sheet within these Excel files. Each sheet is
    then converted to a CSV file and saved in the same directory with a name that combines the
    original file name and the sheet name.
    Example:
        parse_excel_files('/path/to/excel/files')
    """
    for filename in os.listdir(file_path):
        if filename.endswith('.xls') or filename.endswith('.xlsx'):
            file_path_full = os.path.join(file_path, filename)
            print(file_path_full)
            if filename.endswith('.xls'):
                xls = pd.ExcelFile(file_path_full, engine='xlrd')
            else:
                xls = pd.ExcelFile(file_path_full, engine='openpyxl')
            for sheet_name in xls.sheet_names:

                df = pd.read_excel(xls, sheet_name)
                # df = df.applymap(lambda x: x.replace('\t', '') if isinstance(x, str) else x)
                output_filename = f"{os.path.splitext(filename)[0]}_{sheet_name}.csv"
                output_path = os.path.join(file_path, output_filename)
                df.to_csv(output_path, index=False)

# return pandas df given csv path
def csv_to_df(csv_path):
    return pd.DataFrame(pd.read_csv(csv_path, encoding='utf-8'))
    # df = pd.read_csv(csv_path, encoding='utf-8', errors='ignore')

# excel_sheets = pd.ExcelFile(file).sheet_names
def excel_to_df(excel_path):
    df = pd.DataFrame(pd.read_excel(excel_path, sheet_name=pd.ExcelFile(excel_path).sheet_names[-1]))
    return df 

def excel_to_csv(fp):
    # convert all sheet names 
    df = pd.DataFrame(pd.read_excel(fp, sheet_name='PKG South - Barker '))
    df.to_csv(fp)

# return list of sql-processed aggregated column names based on AGG col name prefix 
def get_agg_cols(df):    
    agg_cols = []
    for col in df.columns.tolist():
        if 'agg' in col.lower():
            agg_cols.append(col)
    return agg_cols

def parse_excel_sheets(file):
    # as separate excel files
    print(file)
    excel_sheets = pd.ExcelFile(file).sheet_names

    for sheet in excel_sheets:
        df = pd.DataFrame(pd.read_excel(file, sheet_name=sheet))
        # preprocess drop null rows
        df = df.dropna(how='all')
        csv_file_name = os.path.splitext(file)[0] + '_' + sheet
        print(csv_file_name)
        # output each sheet as it's own .csv file
        df.to_csv(f"{csv_file_name}"+".csv", index=False)

# this is absed on filepaths, the newer code I wrote is based on dataframes
def map_columns(csv1, csv2):
    old_df = csv_to_df(csv1)
    new_df = csv_to_df(csv2)
    old_df = old_df.astype(str)
    new_df = new_df.astype(str)
    old_columns_list = old_df.columns.tolist()  
    new_columns_list = new_df.columns.tolist()
    column_map_dict = {}
    for key, value in zip(old_columns_list, new_columns_list):
        column_map_dict[key] = value
    return column_map_dict

def refact_date_cols(date_str):
    print(type(date_str))
    if pd.isna(date_str):
        return None
    else:
        if isinstance(date_str, datetime):
            date_str = date_str.strftime('%Y-%m-%d')
            print(date_str)
    try:
        # Check if the date_str is a valid date string
    
        # Format the datetime object to mm/dd/yyyy
        date_str = datetime.strptime(date_str, '%Y-%m-%d')
        
    
        formatted_date = date_str.strftime('%m/%d/%Y')
        return formatted_date
    
    except Exception as e:
        print(e, date_str)
        # sys.exit()
        return date_str

# TODO - unify address functions into one 
def city(value):
    try:
        # city
        return usaddress.tag(value)[0]['PlaceName']
    except RepeatedLabelError as e:
        return value.split()[-3]
    except KeyError:
        return None

def state(value):
    try:
        # state
        return usaddress.tag(value)[0]['StateName']
    except usaddress.RepeatedLabelError as e:
        return value.split()[-2]
    except KeyError:
        return None
def zip_code(value):
    try:
        # zip code
        return usaddress.tag(value)[0]['ZipCode']
    except usaddress.RepeatedLabelError as e:
        return value.split()[-1]
    except KeyError:
        return None

# Function to format the date. when excel makes dates in number format, use this function to convert it to a readable date
def format_excel_date(excel_date):
    # handle if data looks like: 2019-07-23 00:00:00
    if isinstance(excel_date, str) and re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', excel_date):
        try:
            date = datetime.strptime(excel_date, '%Y-%m-%d %H:%M:%S')
            return date.strftime('%m/%d/%Y')
        except ValueError:
            return excel_date

    # handle if data looks like: 2024-03-29
    if isinstance(excel_date, str) and re.match(r'\d{4}-\d{2}-\d{2}', excel_date):
        try:
            date = datetime.strptime(excel_date, '%Y-%m-%d')
            return date.strftime('%m/%d/%Y')
        except ValueError:
            return excel_date
        
    if isinstance(excel_date, str):
        try:
            excel_date = int(excel_date)
        except ValueError:
            return excel_date
        date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + excel_date - 2)
        return date.strftime('%m/%d/%Y')
    
    if isinstance(excel_date, float):
        return excel_date

# Handle pd.Timestamp refact_date_cols_pd
# used by monster.py and divvy.py
def pd_timestamp_to_cubbs_date(date_str):
    print(type(date_str))
    if isinstance(date_str, pd._libs.tslibs.timestamps.Timestamp):
        date_str = date_str.strftime('%Y-%m-%d')
    try:
        if isinstance(date_str, str):
            # Format the datetime object to mm/dd/yyyy
            date_str = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_str.strftime('%m/%d/%Y')
            return formatted_date
    
    except Exception as e:
        print(e, date_str)
        # sys.exit()
        return date_str

def get_currencies():

    try:
        # print(os.getenv('CURRENCY_API_KEY'))
        # sys.exit()
        if 'currency_quotes.txt' not in os.listdir():
            # url = "http://api.currencylayer.com/live?access_key=e4c1b4717d070bba428a5209062ab1c7"
            url = "http://api.currencylayer.com/live?access_key=f0bdfd007920903d1482b46252f416b7"

            payload = {}
            headers = {
                'Authorization': os.getenv('CURRENCY_API_KEY') 
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            print(response)
            quotes = json.loads(response.text)["quotes"]
            with open('currency_quotes.txt', 'w') as file:
                json.dump(quotes, file, indent=4)
        else: 
            # READ QUOTES FROM FILE
            with open('currency_quotes.txt', 'r') as file:
                quotes = json.load(file)

        return quotes
    except Exception as e:
        print(f"An error occurred: {e}")

# This function converts a tsv file to a csv file
def convert_tsv_to_csv(tsv_file_path, csv_file_path):
    
    with open(tsv_file_path, 'r', newline='') as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        with open(csv_file_path, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            for row in tsv_reader:
                csv_writer.writerow(row)


def convert_state_to_abbreviation(state_name):
    state_abbreviations = {
                'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
                'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
                'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
                'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD', 'massachusetts': 'MA',
                'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO', 'montana': 'MT',
                'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM',
                'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
                'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD',
                'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA',
                'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY', 'puerto rico': 'PR', 'guam': 'GU'
            }
    try:
        if isinstance(state_name, str):
            state_name = state_name.lower()
            if state_name.upper() in state_abbreviations.values():
                return state_name.upper()
            elif state_name in state_abbreviations:
                return state_abbreviations[state_name]
            else:
                return state_name

    except KeyError:
        print(f"State name '{state_name}' not found in the dictionary.")
        return state_name
