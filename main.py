import pandas as pd
from pyweb import pydom
from pyodide.http import open_url
from pyscript import display
import js
from js import console
from js import window, document  # Import the `window` object from the `js` module
import sys

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
    
    df = pd.read_csv(open_url(url))

    # Manipulate the DataFrame by adding "FOO" as a prefix to the first column
    first_col = df.columns[0]
    
    df[first_col] = "FOO" + df[first_col].astype(str)

    pydom["div#pandas-output"].style["display"] = "block"
    pydom["div#pandas-dev-console"].style["display"] = "block"

    display(df, target="pandas-output-inner", append="False")

def download_csv(df):

    # Convert DataFrame to CSV string
    csv_string = df.to_csv(index=False)

    # Create a Blob object for the CSV data
    blob = js.Blob.new([csv_string], { "type": "text/csv" })

    # Create a URL for the Blob
    url = js.window.URL.createObjectURL(blob)

    # Create a temporary link element
    link = js.document.createElement("a")
    link.href = url
    link.download = "transformed_data.csv"  # File name for download

    # Programmatically click the link to trigger the download
    js.document.body.appendChild(link)
    link.click()

    # Remove the temporary link element
    js.document.body.removeChild(link)
    js.window.URL.revokeObjectURL(url)

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
                from io import StringIO
                df = pd.read_csv(StringIO(content))
                first_col = df.columns[0]
                df[first_col] = "FOO" + df[first_col].astype(str)
                
                pydom["div#pandas-output"].style["display"] = "block"
                pydom["div#pandas-dev-console"].style["display"] = "block"
                display(df, target="pandas-output-inner", append=False)

                # Show the download button and bind the click event
                download_csv(df)

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