# Standard library imports
import re
import sys
from datetime import datetime
import shutil

# Third-party imports
import pandas as pd
import usaddress
from usaddress import RepeatedLabelError
from nameparser import HumanName

sys.path.insert(0, 'python_files')
# Local imports
import dynamic_tsv

from io import StringIO
from js import document, window

# Create a Blob and trigger download
# blob = window.Blob.new([csv_content], {"type": "text/csv"})
# url = window.URL.createObjectURL(blob)
# link = document.createElement("a")
# link.href = url
# link.download = "data.csv"
# document.body.appendChild(link)
# link.click()
# document.body.removeChild(link)
# window.URL.revokeObjectURL(url)


def parse_line(line):
    print(line)
    input_string = re.sub(r'\s+', ' ', line)

    # simplify regex patterns to get everything from the left most index of the string until the matching end signal pattern
    regex_patterns = [r'^([A-Z]{4}\d{6})',
                    r'([A-Za-z\s.\'\&\-]+)',
                    # 7155 W 91ST ST APT 1W BRIDGEVIEW IL604550000000007085398253 02/09/2406/24/24AP3743 HARLEM INSURANCE AGENCY INC. 7089239500000138.33FI
                    r'^(.*?)\s[A-Z]{2}\d{5}',
                    # phone number
                    r'0{9}(\d{10})',
                    # date1
                    r'(\d{2}/\d{2}/\d{2})',
                    # date2
                    r'(\d{2}/\d{2}/\d{2})',
                    # insurance company name 
                    r"([A-Za-z\s.,'&:/\d-]+)\s(?=\d+\.\d{2}[A-Z]{2})",
                    # balance A15
                    r'^(\d{10})',       
                    ]
    data = []

    for pattern in regex_patterns:

        # if pattern index == 6 (insurance company name), drop the characters before the first space character
        if regex_patterns.index(pattern) == 6:
            input_string = input_string.split(' ', 1)[1]
            #print(input_string)
            #sys.exit()
        # print(input_string)        
        match = re.search(pattern, input_string)
        if match:
            # print(match)
            # print(match.group(0))
            data.append(match.group(0))

        else:
            print(input_string)
            index_=regex_patterns.index(pattern)
            print(index_)
            data.append("None")

        # remove leading and trailing spaces from the input string
        if match is not None:
            input_string = input_string.replace(match.group(0), '', 1).strip()
        # input_string = input_string.replace(match.group(0), '', 1).strip()
        # print(input_string)

    result_dict = {
        'A11': data[0],
        'A2.1': data[1],
        # separate the two letter state code and zip code OH44310 > OH 44310
        'A3.1': data[2],
        # todo: strip leading 0's
        'A8': data[3],
        # policy effective date (CHARGE DATE) (consumer columns: 285, 286, 287)
        'A12': data[4],
        # chargeoff date
        'F285': data[5],
        'M1': 'INS AGT: '+data[6],
        'M2': data[7],
        'A15': input_string # remaining string
    }

    return result_dict

def reformat_A15(value):
    # Remove 'FI' postfix
    value = str(value)
    value = value.replace('FI', '')
    # Remove leading zeros
    value = value.lstrip('0')
    return value

def reformat_names(value):
    name = HumanName(value)
    formatted_name = f"{name.last}, {name.suffix} {name.title} {name.first} {name.middle}"
    # remove extra spaces in formatted name
    formatted_name = re.sub(r'\s+', ' ', formatted_name).strip()
    return formatted_name

# reformat A8 values to remove leading zeros
def reformat_A8(value):
    return value.lstrip('0')

def reformat_address(value):
    try:
        # addr_dict = {}
        # add a space at index -6
        value = value[: -5] + " " + value[-5:]
        print(value)
        return ' '.join(usaddress.tag(value)[0].values())
    except usaddress.RepeatedLabelError as e:
        return value

    # # street address
    # # everything before placename
    # addr_dict['A3.1'] = value[:usaddress.tag(value)[0]['PlaceName']]
    # # city
    # addr_dict['A4'] = usaddress.tag(value)[0]['PlaceName']
    # # state
    # addr_dict['A5'] = usaddress.tag(value)[0]['StateName']
    # # zip code
    # addr_dict['A6'] = usaddress.tag(value)[0]['ZipCode']

# return addr_dict
# print(' '.join(usaddress.tag(input_string)[0].values()))
def city(value):
    try:
        # city
        return usaddress.tag(value)[0]['PlaceName']
    except usaddress.RepeatedLabelError as e:
        return value.split()[-3]
    except KeyError:
        return None

def state(value):
    try:
        # state
        return usaddress.tag(value)[0]['StateName']
    except usaddress.RepeatedLabelError as e:
        return value.split()[-2]

def zip_code(value):
    try:
        # zip code
        return usaddress.tag(value)[0]['ZipCode']
    except usaddress.RepeatedLabelError as e:
        return value.split()[-1]

# remove everything from placename onward
def final_address(value):
    try:
        # from the index where placename starts, remove everything after
        value = value[:value.find(usaddress.tag(value)[0]['PlaceName'])]
        return value.strip()
    except usaddress.RepeatedLabelError:
        return ' '.join(value.split()[:-3])
    except KeyError:
        return None
    
import os

def loop(content):
    final_dict = []
    
    final_dict = [parse_line(line) for line in content.splitlines()]
    df = pd.DataFrame(final_dict)

    df['A15'] = df['A15'].apply(reformat_A15)
    df = df[df['A15'].astype(float) >= 50.00]
    df['A2.1'] = df['A2.1'].apply(reformat_names)
    df['A8'] = df['A8'].apply(reformat_A8)
    # format address first time
    df['A3.1'] = df['A3.1'].apply(reformat_address)
    df['A4'] = df['A3.1'].apply(city)
    df['A5'] = df['A3.1'].apply(state)
    df['A6'] = df['A3.1'].apply(zip_code)
    # format address second time
    df['A3.1'] = df['A3.1'].apply(final_address)
    df['F286'] = 'CHARGE OFF DATE'
    
    # F287: principal amount, 99% of time. maybe interest barren, or fees.
    # if that's case, populate F288 (interest), F289 (fees)
    # F290 subsequent charges
    df['F287'] = df['A15']
    df['F288'] = 0.0
    df['F289'] = 0.0
    df['F290'] = 0.0
    
    # put A15 after A12
    df.insert(loc=3, column='A4', value=df.pop('A4'))
    df.insert(loc=4, column='A5', value=df.pop('A5'))
    df.insert(loc=5, column='A6', value=df.pop('A6'))
    df.insert(loc=8, column='A15', value=df.pop('A15'))
    df.insert(loc=9, column='F286', value=df.pop('F286'))
    #address dataframe: merge at end
    # addr_df = df.apply(lambda x: reformat_address(x['A3.1']), result_type='expand')
    df = df.rename(columns={'M1': 'M', 'M2': 'M'})
    # df.to_csv(f'{file_name}.csv', index=False)
  
    # df = pd.DataFrame()
    # final_dict = []

    # Move the placement files into the new directory

    # placement_file_names = [name + '.csv' for name in placement_file_names]

    # dynamic_tsv.dynamic_tsv(placement_file_names)
        
    # for file_name in placement_file_names:
    #     original_file_name = file_name.replace('.csv', '')
    #     # just get the base tsv file name 
    #     tsv_file_name = file_name.replace('.csv', '.tsv')

    #     # Move the files to the new dated directory
    #     # original raw file
    #     shutil.move(original_file_name, new_directory)
    #     # csv file
    #     shutil.move(file_name, new_directory)
    #     # tsv file
    #     shutil.move(tsv_file_name, new_directory)

    #     # variable for renaming to FOUNDERS.tsv
    #     tsv_file_base_name = os.path.basename(tsv_file_name)
    #     os.rename(os.path.join(new_directory, tsv_file_base_name), os.path.join(new_directory, 'FOUNDERS.tsv'))
        
    return df
        
        # # Rename the tsv file to FOUNDERS.tsv based on Anitha's request

loop()
