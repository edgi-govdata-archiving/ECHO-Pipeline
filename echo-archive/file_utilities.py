import json
import requests
import os
import zipfile
import tarfile
import gzip
import shutil
import logging

def store_entry(key, metadata_entry, metadata_file):
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

    if key not in data.keys():
        data[key] = {}
    for new_key, new_value in metadata_entry.items():
        data[key][new_key] = new_value

    # Write the updated data back to the file
    with open(metadata_store, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        print(f"File '{metadata_store}' updated successfully.")

def check_if_path_exists(path):
    if os.path.exists(path):
        logging.info(f'{path} already exists, skipping')
        return True
    return False


def create_directory(directory):
    os.makedirs(directory, exist_ok=True)


def extract_file(url, temp_path, destination_dir):
    try:
        # Determine file type and process
        if url.endswith(".zip"):
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                for file in file_list:
                    if check_if_path_exists(os.path.join(destination_dir, file)):
                        print('file already exists')
                        continue
                    else:
                        zip_ref.extract(file, destination_dir)

                # zip_ref.extractall(destination_dir)
            logging.info(f"Extracted ZIP contents to {destination_dir}")
        elif url.endswith(".tar.gz") or url.endswith(".tgz"):
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall(destination_dir)
            logging.info(f"Extracted TAR.GZ contents to {destination_dir}")
        elif url.endswith(".gz"):
            output_file = os.path.join(destination_dir, os.path.basename(url).replace(".gz", ""))  # Remove .gz
            with gzip.open(temp_path, 'rb') as gz_file:
                with open(output_file, 'wb') as out_file:
                    shutil.copyfileobj(gz_file, out_file)
            logging.info(f"Extracted GZ file to {output_file}")
    except (zipfile.BadZipFile, tarfile.TarError, gzip.BadGzipFile) as e:
        logging.error(f"Failed to extract compressed file {url}: {e}")


def download_file(url, destination_dir, last_modified_timestamp, need_extracting=False):
    create_directory(destination_dir)
    file_name = os.path.basename(url)

    temp_path = os.path.join(destination_dir, "temporary")
    logging.info("Proceed with downloading or extracting the file.")

    try:
        logging.info(f"Starting download from {url}")
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()
        with open(temp_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info(f"Downloaded file from {url} to {temp_path}")

        if need_extracting == True and url.endswith(".zip"):
            extract_file(url, temp_path, destination_dir)
        else:
            final_path = os.path.join(destination_dir, file_name)
            shutil.move(temp_path, final_path)

            # Change last modified time to what's on the echo server #
            os.utime(final_path, (last_modified_timestamp, last_modified_timestamp))

            logging.info(f"Saved file to {final_path}")
    except requests.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def store_file(contents, name, directory):
    os.makedirs(directory, exist_ok=True)
    path_to_store = os.path.join(directory, name)
    with open(path_to_store, "w", encoding="utf-8") as file:
        file.write(contents)
    print(f"Content successfully saved to {path_to_store}")
    return name