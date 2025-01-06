import pandas as pd
from pyweb import pydom
from pyodide.http import open_url
from pyscript import display
import js
from js import console
from js import window, document  # Import the `window` object from the `js` module
import sys, os
import re

# sys.path.insert(0, '/workspaces/pyscript-pages-test/')
# sys.path.append('/workspaces/pyscript-pages-test/founders_web.py')
# import founders_web

title = "Pandas (and basic DOM manipulation)"
page_message = "This example loads a remote CSV file into a Pandas dataframe, and displays it."

client_urls = {
    "Founders": "https://raw.githubusercontent.com/datasets/airport-codes/master/data/airport-codes.csv",
    "Cryosell": "https://people.sc.fsu.edu/~jburkardt/data/csv/hw_200.csv"
}

default_url = client_urls["Founders"]

pydom["title#header-title"].html = title
pydom["a#page-title"].html = title
pydom["div#page-message"].html = page_message
pydom["input#txt-url"][0].value = default_url

# Create dropdown for client selection
# Add dropdown widget dynamically
# client_dropdown_html = "<select id='client-dropdown'>" + "".join(
#     f"<option value='{url}'>{client}</option>" for client, url in client_urls.items()
# ) + "</select>"

# pydom["div#client-dropdown"].html = client_dropdown_html
# pydom["div#file-input-container"].html = file_input_html
        
def log(message):
    # log to pandas dev console
    print(message)
    # log to JS console
    console.log(message)

def updateURL(event):
    # selected_client: List data type of length 1  
    selected_client = pydom["select#client-selector"].value

def loadFromURL(event):
    pydom["div#pandas-output-inner"].html = ""
    selected_client = pydom["select#client-selector"].value

    if selected_client[0] == "founders":
       
        url = pydom["input#txt-url"][0].value
        pydom["input#txt-url"][0].value = client_urls["Founders"]

        # url = client_urls["Flounders"]

    if selected_client[0] == "cryosell":
        url = pydom["input#txt-url"][0].value
        pydom["input#txt-url"][0].value = client_urls["Cryosell"]
        # url = client_urls["Biocell"]
        
    log(f"Selected client: {selected_client}")
    log(f"Trying to fetch CSV from {url}")
    # log("Current working directory:", os.getcwd())
    
    df = pd.read_csv(open_url(url))

    # Manipulate the DataFrame by adding "FOO" as a prefix to the first column
    first_col = df.columns[0]
    
    df[first_col] = "FOO" + df[first_col].astype(str)

    pydom["div#pandas-output"].style["display"] = "block"
    pydom["div#pandas-dev-console"].style["display"] = "block"

    display(df, target="pandas-output-inner", append="False")

def download_founders_tsv(df):
    import js

    # Convert DataFrame to CSV string
    tsv_string = df.to_csv(index=False, sep="\t") # Set sep='\t' for TSV format
    # Create a Blob object for the TSV data
    blob = js.Blob.new([tsv_string], { "type": "text/tab-separated-values" })

    # Create a URL for the Blob
    url = js.window.URL.createObjectURL(blob)

    # Create a temporary link element
    link = js.document.createElement("a")
    link.href = url
    link.download = "FOUNDERS.tsv"  # File name for download

    # Programmatically click the link to trigger the download
    js.document.body.appendChild(link)
    link.click()

    # Remove the temporary link element
    js.document.body.removeChild(link)
    js.window.URL.revokeObjectURL(url)

# import usaddress
# from usaddress import RepeatedLabelError
# from nameparser import HumanName

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

# # reformat A8 values to remove leading zeros
def reformat_A8(value):
    return value.lstrip('0')

def city(addr_col):
    try:
        address_list = addr_col.split(" ")
        print(address_list)
        city = address_list[-2]
        return city  
    except Exception as e:
        return None
        
def state(addr_col):
    try:
        address_list = addr_col.split(" ")
        print(address_list)
        state = address_list[-1][0:2]
        return state        
    except Exception as e:
        return None
        
def zip(addr_col):
    try:
        address_list = addr_col.split(" ")
        zip = address_list[-1][2:]
        return zip
    except Exception as e:
        return None

def founders_parse(content):
    final_dict = []
    
    final_dict = [parse_line(line) for line in content.splitlines()]
    df = pd.DataFrame(final_dict)

    df['A15'] = df['A15'].apply(reformat_A15)
    df = df[df['A15'].astype(float) >= 50.00]
    # df['A2.1'] = df['A2.1'].apply(reformat_names)
    df['A8'] = df['A8'].apply(reformat_A8)
    # format address first time
    
    # df['A3.1'] = df['A3.1'].apply(reformat_address)

    df['A4'] = df['A3.1'].apply(city)
    df['A5'] = df['A3.1'].apply(state)
    df['A6'] = df['A3.1'].apply(zip)
    
    # format address second time
    # df['A3.1'] = df['A3.1'].apply(final_address)
    df['F286'] = 'CHARGE OFF DATE'
    
    # F287: principal amount, 99% of time. maybe interest barren, or fees.
    # if that's case, populate F288 (interest), F289 (fees)
    # F290 subsequent charges
    df['F287'] = df['A15']
    df['F288'] = 0.0
    df['F289'] = 0.0
    df['F290'] = 0.0
    
    # put A15 after A12
    if 'A4' in df.columns:
        df.insert(loc=3, column='A4', value=df.pop('A4'))
    if 'A5' in df.columns:
        df.insert(loc=4, column='A5', value=df.pop('A5'))
    if 'A6' in df.columns:
        df.insert(loc=5, column='A6', value=df.pop('A6'))
    if 'A15' in df.columns:
        df.insert(loc=8, column='A15', value=df.pop('A15'))
    if 'F286' in df.columns:
        df.insert(loc=9, column='F286', value=df.pop('F286'))
    
    #address dataframe: merge at end
    # addr_df = df.apply(lambda x: reformat_address(x['A3.1']), result_type='expand')
    df = df.rename(columns={'M1': 'M', 'M2': 'M'})

    return df
            
# # Rename the tsv file to FOUNDERS.tsv based on Anitha's request
def loadFromFile(event):
    pydom["div#pandas-output-inner"].html = ""
    selected_client = pydom["select#client-selector"].value

    file_input = js.document.getElementById("file-input")

    if file_input.files.length == 0:
        log("No file selected.")
        return

    file = file_input.files.item(0)
    log(f"Selected file: {file.name}")

    try:
        file_reader = js.window.FileReader.new()

        def onload(event):
            content = event.target.result
            try:
                # from io import StringIO
                
                # Test transform
                # df = pd.read_csv(StringIO(content))
                # first_col = df.columns[0]
                # df[first_col] = "FOO" + df[first_col].astype(str)
                
                # Founders transform
                print(f"Content type: {type(content)}")
                print(f"Content preview: {content[:500]}")
                
                df = founders_parse(content)
                
                pydom["div#pandas-output"].style["display"] = "block"
                pydom["div#pandas-dev-console"].style["display"] = "block"
                
                display(df, target="pandas-output-inner", append=False)

                # Show the download button and bind the click event
                download_founders_tsv(df)

            except Exception as e:
                log(f"Error parsing CSV: {e}")

        file_reader.onload = onload
        file_reader.readAsText(file)
    except Exception as e:
        log(f"Error reading file: {e}")

# Attach the updateURL function to the dropdown change event
pydom["select#client-selector"].on("change", updateURL)

# Attach event listener to the load button
pydom["#btn-csv-load"].on("click", loadFromFile)


