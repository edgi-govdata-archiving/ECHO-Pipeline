import json
import queue
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import urllib3
import os
import logging
from file_utilities import *

# Configure logging
log_dir = '../cleaned_directory/logs'
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

# Error about site certificate not being valid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def is_file(url):
    try:
        # Send a HEAD request to get headers without downloading the content
        response = requests.head(url, allow_redirects=True, verify=False)
        # Check the content type in the headers
        if 'Content-Type' in response.headers:
            # If the content type is not a directory, assume it's a file
            content_type = response.headers['Content-Type']
            if 'text/html' in content_type:
                # For directories, the content type might be HTML or redirected (could point to a listing page)
                return False
            return True

        # If no content type, it could be a directory (like when it returns a listing page)
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking URL: {e}")
        return -1


def fetch_links(url):
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: {response.status_code}")

    soup = BeautifulSoup(response.content, "html.parser")
    table_rows = soup.find('table').find_all('tr')
    return table_rows


def convert_to_mb(size_str):
    if size_str == '-':
        return size_str
    # Extract the number and unit from the string
    size, unit = float(size_str[:-1]), size_str[-1].upper()
    if unit.isdigit():
        return size_str
    # Convert the size to bytes based on the unit
    if unit == 'K':
        size_in_bytes = size * 1024  # 1 KB = 1024 bytes
    elif unit == 'M':
        size_in_bytes = size * 1024 ** 2  # 1 MB = 1024^2 bytes
    elif unit == 'G':
        size_in_bytes = size * 1024 ** 3  # 1 GB = 1024^3 bytes
    else:
        raise ValueError(f"Unsupported unit: {unit}")

    # Convert bytes to megabytes
    size_in_mb = size_in_bytes / 1024 ** 2
    return f'{size_in_mb:.2f}'


def log_error_files(contents):
    error_file = 'errors'
    if not os.path.exists(error_file):
        with open(error_file, "w", encoding="utf-8") as file:
            file.write(contents)
    else:
        with open(error_file, "a", encoding="utf-8") as file:
            file.write(contents)


def crawl_page(base_url, metadata_file):
    # Initialize a queue to manage URLs to be processed
    q = queue.Queue()
    q.put(base_url)
    files = {}

    # Process URLs in the queue until it's empty
    while not q.empty():
        url = q.get()
        logging.info(url)
        try:
            rows = fetch_links(url)
        except Exception as e:
            logging.error(f"Error fetching links from {url}: {e}")
            continue

        # Iterate over each row in the fetched table
        for row in rows:
            # Find the anchor tag with a href attribute
            a_tag = row.find('a', href=True)
            if not a_tag:
                continue
            if a_tag.text.strip() == 'Parent Directory' or a_tag.text.strip() == 'Name':
                continue

            # Extract the href link and construct the full URL
            link = a_tag['href']
            full_url = urljoin(url, a_tag['href'])
            # print(full_url)

            cells = row.find_all('td', align='right')
            timestamp = cells[0].text.strip() if len(cells) > 0 else None  # Extract timestamp if available
            size = convert_to_mb(cells[1].text.strip()) if len(cells) > 1 else None  # Extract size if available

            # Check if the link points to a file or directory
            file_check = is_file(full_url)
            if file_check is None:
                logging.warning(f'Unable to determine if {full_url} is a file or directory')
                continue
            # If it's a directory, add its URL to the queue for processing
            elif not file_check:
                logging.info(f'{full_url} is a directory')
                q.put(full_url)
            else:
                logging.info(f'{full_url} is a file, adding to list')
                file_info = {
                    'name': link,  # Name of the file
                    'link': full_url,  # Full URL to the file
                    'timestamp': timestamp,  # Timestamp of the file if available
                    'size(mb)': size  # Size of the file if available
                }
                # If it's a file, append its information to the files list
                files[link] = file_info

                store_entry(link, file_info, metadata_file)
    # Return the collected list of file information
    return files


def main():
    # Base URL of the website
    BASE_URL = "https://echo.epa.gov/files/echodownloads/"
    METADATA_FILE = "datasets_metadata.json"
    FILES_TO_DOWNLOAD = "dataset_and_schema_links.txt"
    ERROR_FILE = "errors.json"
    BASE_LOCAL_PATH = "data/datasets"
    OPTION = FILES_TO_DOWNLOAD

    try:
        if OPTION == METADATA_FILE:  # Change this depending on if we want to archive whole site or just specific filess
            urls = crawl_page(BASE_URL, METADATA_FILE)
            logging.info(f'Done scraping {BASE_URL}')
            logging.info(f'Beginning file download')

            data = {}
            with open(METADATA_FILE, "r", encoding="utf-8") as output_file:
                data = json.load(output_file)
            print(data)

            for file_name, file in data.items():
                try:
                    parsed_url = urlparse(file['link'])
                    file_path = parsed_url.path.lstrip('/')  # Remove leading '/' to avoid issues
                    if file_name.endswith(".zip"):
                        download_file(file['link'], os.path.join(BASE_LOCAL_PATH, file_name), need_extracting=True)
                    else:
                        download_file(file['link'], os.path.join(BASE_LOCAL_PATH), need_extracting=False)

                except Exception as download_error:
                    logging.error(f"Error downloading {file['link']}: {download_error}")
                    log_error_files(f"{file['link']}: {download_error}")
                    continue
        else:

            data = []
            with open(FILES_TO_DOWNLOAD, "r", encoding="utf-8") as in_file:
                for line in in_file:
                    data.append(line.strip().split(",")[0])
                print(data)
            for url in data:
                file_name = os.path.basename(urlparse(url).path)
                print(file_name)
                try:
                    download_file(url, os.path.join(BASE_LOCAL_PATH), need_extracting=True)
                except Exception as download_error:
                    logging.error(f"Error downloading {url}: {download_error}")
                    log_error_files(f"{url}: {download_error}")
                    continue

    except Exception as e:
        logging.critical(f"Error: {e}")


if __name__ == "__main__":
    main()
