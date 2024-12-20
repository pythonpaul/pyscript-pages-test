import pandas as pd
from pyweb import pydom
from pyscript import display
from js import console

title = "Pandas (and basic DOM manipulation)"
page_message = "This example allows importing a local CSV file into a Pandas dataframe, and displays it."

pydom["title#header-title"].html = title
pydom["a#page-title"].html = title
pydom["div#page-message"].html = page_message

# Add file input widget dynamically
file_input_html = "<input type='file' id='file-input' accept='.csv'>"
pydom["div#dropdown-container"].html = file_input_html

def log(message):
    # log to pandas dev console
    print(message)
    # log to JS console
    console.log(message)

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
        # Parse CSV file into DataFrame
        df = pd.read_csv(file)
        
        # Display the dataframe
        pydom["div#pandas-output"].style["display"] = "block"
        pydom["div#pandas-dev-console"].style["display"] = "block"
        display(df, target="pandas-output-inner", append="False")
    except Exception as e:
        log(f"Error loading file: {e}")

# Attach event listener to the file input
pydom["#file-input"].on("change", loadFromFile)
