import os
import time
import pandas as pd
from schema_utilities import *
from file_utilities import *
import logging

# Configure logging
log_dir = '../logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'echo_dataset_downloader.log')
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)

def get_datasets_schemas(meta_url, notes):
    title = ''
    schemas = {}
    html_file = ''
    if not notes:
        response = requests.get(meta_url)
        if response.status_code != 200:
            print("Error fetching data")
            return

        # Get all tables on site
        title, schemas = parse_schemas(response.text)

        # Save the html file
        html_file = store_file(response.text, f"{title}.html", "data/htmls")
    else:
        filename, worksheet, skiprows = notes.split('-')
        print(filename, worksheet, skiprows)
        rows = []
        df = pd.read_excel(meta_url,
                           sheet_name=worksheet,
                           skiprows=int(skiprows)
                           )
        for index, row in df.iterrows():
            column_name = row['Column Name']
            data_type = row['DATA_TYPE']
            rows.append([column_name, data_type])

        schemas =  [{
            "name": filename,
            "schema": rows
        }]
        html_file = None

    return title, html_file, schemas

def main():
    program_start = time.time()
    urls = []
    logging.info('Gathering all urls')

    with open('dataset_and_schema_links.txt', 'r') as file:
        for line in file:
            links = line.strip().split(",")
            if len(links) > 1:
                urls.append(tuple(links))
                # urls.append((links[0], links[1]))
            else:
                continue
    logging.info('Completed gathering all urls')

    for url_tuple in urls:
        download_url = url_tuple[0] if len(url_tuple) > 0 else None
        meta_url = url_tuple[1] if len(url_tuple) > 1 else None
        notes = url_tuple[2] if len(url_tuple) > 2 else None

        logging.debug(f"processing: {url_tuple[1]}")
        loop_start = time.time()
        title, html_file, dataset_schemas = get_datasets_schemas(meta_url, notes)

        for index, dataset in enumerate(dataset_schemas):
            data_dictionary = {'schema': []}
            logging.debug(f"Table {index}: {dataset['name']}")
            for row in dataset['schema']:
                data_dictionary['schema'].append({"COLUMN_NAME": row[0], "DATA_TYPE": row[1]})
            schema_file_name = f"{dataset['name'].split('.')[0]}_schema.json"
            schema_file = store_file(json.dumps(data_dictionary, indent=4),
                                     schema_file_name,
                                     "data/schemas")
            # Save metadata
            metadata_entry = {'url': meta_url, 'html': html_file, 'schema': schema_file}
            store_entry(dataset['name'], metadata_entry, 'metadata.json')

        logging.debug(f'Done processing {download_url}')
        loop_end = time.time()
        logging.info(f'Time to complete loop: {round(loop_end - loop_start, 2)}')

    program_end = time.time()
    logging.info("Done collecting dataset schemas")
    logging.info(f'Total time: {program_end-program_start}')

if __name__ == '__main__':
    main()