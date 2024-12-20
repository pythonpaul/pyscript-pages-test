import pandas as pd
from pyweb import pydom
from pyodide.http import open_url
from pyscript import display
from js import console

title = "Pandas (and basic DOM manipulation)"
page_message = "This example loads a remote CSV file into a Pandas dataframe, and displays it."
client_urls = {
    "Flounders": "https://raw.githubusercontent.com/datasets/airport-codes/master/data/airport-codes.csv",
    "Biocell": "https://people.sc.fsu.edu/~jburkardt/data/csv/hw_200.csv"
}
default_url = client_urls["Flounders"]

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
    # Update the URL input field based on selected client
    selected_client = pydom["select#client-selector"].value
    console.log(f"Selected client: {selected_client}")
    if selected_client == "flounders":
        pydom["input#txt-url"][0].value = client_urls["Flounders"]
    elif selected_client == "biocell":
        pydom["input#txt-url"][0].value = client_urls["Biocell"]

def loadFromURL(event):
    pydom["div#pandas-output-inner"].html = ""
    url = pydom["input#txt-url"][0].value

    log(f"Trying to fetch CSV from {url}")
    df = pd.read_csv(open_url(url))

    # Manipulate the DataFrame by adding "FOO" as a prefix to the first column
    first_col = df.columns[0]
    df[first_col] = "FOO" + df[first_col].astype(str)

    pydom["div#pandas-output"].style["display"] = "block"
    pydom["div#pandas-dev-console"].style["display"] = "block"

    display(df, target="pandas-output-inner", append="False")

def loadFromFile(event):
    pydom["div#pandas-output-inner"].html = ""
    file_input = pydom["#file-input"][0]
    
    if not file_input.files:
        log("No file selected.")
        return
    
    # Read the file as a CSV
    file = file_input.files[0]
    log(f"Loading file: {file.name}")
    
    try:
        # Read the file content
        content = file.read().decode('utf-8')
        df = pd.read_csv(pd.compat.StringIO(content))
        
        # Display the dataframe
        pydom["div#pandas-output"].style["display"] = "block"
        pydom["div#pandas-dev-console"].style["display"] = "block"
        display(df, target="pandas-output-inner", append="False")
    except Exception as e:
        log(f"Error loading file: {e}")

# Attach the updateURL function to the dropdown change event
pydom["select#client-selector"].on("change", updateURL)

# Attach event listener to the load button
pydom["#btn-csv-load"].on("click", loadFromFile)
