# Libraries
from datetime import datetime
import logging
import requests
import os
import json
from urllib.parse import urlparse


import file_utilities as file_utils
import schema_utilities as schema_utils

# Configure logging
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_file = os.path.join(log_dir, f'{timestamp}.log')
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

# Constants
JSON_FILES_PATH = os.environ['JSON_FILES_PATH']
LOCAL_ECHODOWNLOADS_PATH = os.environ['LOCAL_ECHODOWNLOADS_PATH']
STORAGE_PATH = os.environ['LOCAL_STORAGE_PATH']
LOCAL_UPDATED_DATA_PATH = os.path.join(STORAGE_PATH, 'updated-datasets')
LOCAL_SCHEMA_PATH = os.path.join(STORAGE_PATH, 'schemas')
DATASET_MASTER_LIST = os.path.join(JSON_FILES_PATH, 'dataset_tracker_list.json')

def load_master_list(file_path='dataset_tracker_list.json'):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    updated_files = []
    successful_links = []
    failed_links = []
    master_list = load_master_list(DATASET_MASTER_LIST)
    logger.info('Gathering files to track')

    # DOWNLOADING SECTION #
    for entry in master_list:
        # Get file name from url
        remote_name = urlparse(entry['download_link']).path.split("/")[-1]

        # Check if we've already downloaded the zip file. If we haven't, download it as a temporary zip then remove it
        if os.path.exists(os.path.join(LOCAL_ECHODOWNLOADS_PATH, remote_name)):
            logger.info(f"Found {entry['download_link']} in local echodownloads, extracting the files now")
        
            extracted_files = file_utils.extract_file(entry['download_link'],
                                            os.path.join(LOCAL_ECHODOWNLOADS_PATH, remote_name),
                                            LOCAL_UPDATED_DATA_PATH)
            if extracted_files:
                updated_files.extend(extracted_files)
                
            successful_links.append(remote_name)
        else:
            logger.warning(f"{remote_name} not found in the archive folder. Downloading")
            file_utils.download_file(entry['download_link'], LOCAL_UPDATED_DATA_PATH, datetime.now().timestamp(),
                            need_extracting=True)
            failed_links.append(remote_name)
            
    logger.info(f"Successfully extracted {len(updated_files)} files out of {len(successful_links)} zip files. Zip files: {successful_links}")
    if failed_links:
        logger.warning(f"Failed to extract {len(failed_links)} files. Files: {failed_links} ")
    
    # SCHEMA SECTION #
    for entry in master_list:
        title, html_file, dataset_schemas = schema_utils.get_datasets_schemas(entry['schema_link'], entry['notes'])
        logger.info(f"Parsed and saved schemas from {entry['schema_link']}.")
        for index, dataset in enumerate(dataset_schemas):
            if entry.get('manual_schemas') and dataset['name'] in entry['manual_schemas']:
                logger.warning(f"Found {dataset['name']} in the manual schemas list. Skipping.")
                continue            
            data_dictionary = {"last_modified": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %Z"), "schema": []}
            logger.debug(f"Table {index}: {dataset['name']}")
            for row in dataset['schema']:
                spark_dtype, pd_dtype = schema_utils.map_data_types(row)
                data_dictionary['schema'].append({"COLUMN_NAME": row[0], "ORIGINAL_DATA_TYPE": row[1], "SPARK_DATA_TYPE": spark_dtype, "PANDAS_DATA_TYPE": pd_dtype})
            schema_file_name = f"{dataset['name'].split('.')[0]}_schema.json"
            file_utils.store_file(json.dumps(data_dictionary, indent=4),
                       schema_file_name,
                       LOCAL_SCHEMA_PATH)
            logger.info(f"Successfully stored {schema_file_name}.")

    # Delta Lake container will check for files in data/datasets #


main()