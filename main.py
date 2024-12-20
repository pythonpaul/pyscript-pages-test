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

pydom["title#header-title"].html = title
pydom["a#page-title"].html = title
pydom["div#page-message"].html = page_message

# Add dropdown widget dynamically
dropdown_html = "<select id='client-dropdown'>" + "".join(
    f"<option value='{url}'>{client}</option>" for client, url in client_urls.items()
) + "</select>"
pydom["div#dropdown-container"].html = dropdown_html

# Set initial URL to the first option
initial_url = list(client_urls.values())[0]
pydom["input#txt-url"].value = initial_url

def log(message):
    # log to pandas dev console
    print(message)
    # log to JS console
    console.log(message)

def loadFromURL(event):
    pydom["div#pandas-output-inner"].html = ""
    url = pydom["#client-dropdown"].value

    log(f"Trying to fetch CSV from {url}")
    df = pd.read_csv(open_url(url))

    pydom["div#pandas-output"].style["display"] = "block"
    pydom["div#pandas-dev-console"].style["display"] = "block"

    display(df, target="pandas-output-inner", append="False")

# Attach event listener to dropdown
pydom["#client-dropdown"].on("change", loadFromURL)
