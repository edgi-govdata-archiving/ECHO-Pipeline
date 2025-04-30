from bs4 import BeautifulSoup
import pandas as pd
import requests
import os
import json
import re
import logging

from file_utilities import store_file

logger = logging.getLogger(__name__)

def get_table_names(elements):
    table_names = []
    for tag in elements:
        matches = re.findall(r'\(([^)]+\.csv)\)', tag.text)  # Match text inside parentheses
        if not matches:
            print(f'No match in {tag.text}')
            continue
        table_names.append(matches[0])
    print(f'Found potential {len(table_names)} schema tables')
    return table_names

def get_tables(soup):
    required_headers = ['Element Name', 'Element']
    # Find all tables
    table_contents = soup.find_all("table")
    if not table_contents:
        raise ValueError("No tables found in the provided HTML.")

    tables = []
    # print('number of tables in the page ', len(table_contents))
    # Remove unwanted tables
    for table in table_contents:
        # print(table)
        thead = table.find("thead")
        if not thead:
            # print('doesnt have header')
            continue

        header_row = thead.find("tr")
        headers = [th.text.strip() for th in header_row.find_all("th")]

        # Check for headers of schema tables only
        if not any(header in headers for header in required_headers):
            # print('not the table we need')
            continue

        tables.append(table)

    return tables

def parse_schemas(html: str):
    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Get title of webpage
    title = soup.find("h1").text.strip()
    # print('title of webpage: ', title)

    # Get names of all table on the webpage
    h3_tags = soup.find_all("h3")
    table_names = get_table_names(h3_tags)

    tables = get_tables(soup)
    # print('number of tables with schema info ', len(tables))
    # Iterate over each table
    results = []
    for name, table in zip(table_names, tables):
        # print('table: ', name)

        # Extract table rows
        rows = []
        tbody = table.find("tbody")
        if tbody:
            for row in tbody.find_all("tr"):
                cells = [cell.text.strip().lower() for cell in row.find_all("td")]
                cells = [cell[:-1] if cell and cell[-1].isdigit() else cell for cell in cells]
                rows.append(cells)

        # Append the table's data
        results.append({
            "name": name,
            "schema": rows
        })
    #     print('Done scraping table: ', name)
    # print(f'tables : {len(results)}')
    # print(f'table names: {len(table_names)}')
    return title, results


def store_metadata_entry(key, metadata_entry, metadata_file):
    metadata_store = metadata_file
    # Check if the file exists
    if not os.path.exists(metadata_store):
        # Create an empty JSON file with default data
        with open(metadata_store, "w", encoding="utf-8") as file:
            json.dump({}, file)
        print(f"File '{metadata_store}' created.")

    # Read the JSON file
    with open(metadata_store, "r", encoding="utf-8") as file:
        data = json.load(file)  # Load the JSON data

    data[key] = metadata_entry

    # Write the updated data back to the file
    with open(metadata_store, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        print(f"File '{metadata_store}' updated successfully.")

def map_data_types(schema_row):
    column_name, column_type = schema_row[0], schema_row[1]

    if 'id' in column_name and column_type in {"num", "number"}:
        return "LongType()", "int64"
    elif column_type in {"num", "number"}:
        return "DoubleType()", "float64"
    elif column_type in {"char", "varchar", "varchar2", "date"}:
        return "StringType()", "str"
    else:
        logger.warning(f"Warning: Unsupported data type {column_type} for column {column_name}, defaulting to StringType")
        return "StringType()", "str"

def get_datasets_schemas(meta_url, notes):
    title = ''
    schemas = {}
    html_file = ''
    if not notes:
        response = requests.get(meta_url)
        if response.status_code != 200:
            logger.exception("Error fetching data. Error: {e}")
            return False

        # Get all tables on site
        title, schemas = parse_schemas(response.text)
        logger.info(f"Parsed {len(schemas)} schemas out of {meta_url}.")

        # Save the html file
        html_file = store_file(response.text, f"{title}.html", "data/htmls")
        logger.info(f"Saved {title} as a html file.")
    else:
        filename, worksheet, skiprows = notes.split('-')
        print(filename, worksheet, skiprows)
        rows = []
        df = pd.read_excel(meta_url,
                           sheet_name=worksheet,
                           skiprows=int(skiprows)
                           )
        for index, row in df.iterrows():
            column_name = row['Column Name'].strip().lower()
            data_type = row['DATA_TYPE'].strip().lower()
            rows.append([column_name, data_type])

        schemas =  [{
            "name": filename.upper(),
            "schema": rows
        }]
        html_file = None
        logger.info("Got schema from echo exporter excel file.")

    return title, html_file, schemas

def replace_text(text, schema_file):
    """Replace occurrences of keys in text based on the replacements dictionary."""
    # Load in schema corrections
    replacements =  json.load(open('schema_fixes.json'))
    fixes = replacements.get(schema_file)
    if fixes:
        for pair in fixes:
            for key, value in pair.items():
                text = text.replace(key, value)
    return text