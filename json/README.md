# JSON

## Overview
This folder contains:

- JSON schema files used to define the structure of CSV files before ingestion into Delta Lake.
- Additional JSON configuration files used by other components of the application.

## Folder Structure

    schemas/
    ├── CASE_DEFENDANTS_schema.json
    ├── CASE_ENFORCEMENT_schema.json
    ├── ECHO_EXPORTER_schema.json
    └── ...
    dataset_tracker_list.json
    schema_csv_mapping.json
    spark_materialized_views.json

## Files Overview
### Schema Files (for Delta Lake Ingestion)
These files define the columns and data types expected when loading CSVs into Delta Lake.

Each schema file follows this format:
```json
{
    "last_modified": "timestamp of the last schema modification",
    "schema": [
        {
            "COLUMN_NAME": "name_of_the_column",
            "ORIGINAL_DATA_TYPE": "data_type_from_epa_schema",
            "SPARK_DATA_TYPE": "spark_data_type_for_ingestion",
            "PANDAS_DATA_TYPE": "python_pandas_data_type"
        }
    ]
}
```
where 
- last_modified: A timestamp indicating when the schema was last updated
- schema: A list of column definitions where each object describes details of a column:
    - COLUMN_NAME: The name of the column in the dataset.
    - ORIGINAL_DATA_TYPE: The data type described by the EPA's original schema.
    - SPARK_DATA_TYPE: The data type for Spark, ensuring correct ingestion of the data.
    - PANDAS_DATA_TYPE: The data type used when converting the Spark DataFrame to a Pandas DataFrame.

### Adding New Schema File
1. Create a new JSON file inside the `schemas/` folder following the format described above.
2. Add the `last_modified` timestamp.
3. List the columns in order that they appear in the CSV.

## Dataset Master List (`dataset_tracker_list.json`)
### Overview

A master list that defines all external datasets the ECHO pipeline scrapes and stores. Each entry includes:
- download_link: URL to download the dataset ZIP or CSV.
- schema_link: URL pointing to a webpage containing the schema description.
- manual_schemas: List of CSV files that must be manually handled
- notes: Optional notes about special handling or dataset quirks.

This file controls what datasets the system monitors and how they are processed.

(Some CSVs require manual schema definitions because the script cannot correctly generate a structure due to differences in webpage structures.)

### Adding new datasets to pipeline
1. Open `dataset_tracker_list.json`.
2. Write a new entry in the file following the format above and be sure to specify the filename in the `manual_schemas` if the schema webpage does not follow the structure of the pages that work.

## Linking CSV file to a Schema (`schema_csv_mapping.json`)
### Overview

A mapping file that links each CSV filename to its corresponding JSON schema file. It ensures that the ingestion script applies the correct schema when reading each CSV into Delta Lake.

Each entry typically looks like:

```json
"{csv_file}": "{schema_file}"
```
where:
- csv_file: The name of the CSV file.
- schema_file: The name of the JSON schema file to use.

This mapping allows the data ingestion process to dynamically load and apply the correct schema without hardcoding file relationships.
It also allows users to control which files are ingested into the system.

### Adding a new link
After adding a new dataset to echo pipeline, you need to link the new CSV files with the associated schemas. To ensure the scripts save the CSV files to delta tables:

1. Open `schema_csv_mapping.json`.
2. Add a new entry mapping the CSV filename to the corresponding schema filename like the format described above.
3. Run `savetolake.py` and the newly added files will now become Delta Tables.

## Creating Materialized Views (`spark_materialized_views.json`)
### Overview

A collection of predefined Spark SQL queries used to create materialized views (filtered or transformed versions of raw tables) inside Delta Lake. An entry looks like the following:

```json
"{materialized_view_name}": {
        "statements": [
            "SQL Query 1"
        ],
        "tables": [
            "table_1",
            "table_2",
            "table_3"
        ]
    },

```
where 
- materialized_view_name: The name of the materialized view.
- statements: The SQL statement that defines the view.
- tables: The base tables needed to create the view

These views are used to optimize and accelerate frequent analytics queries on ingested datasets. 
### Add a new materialized view
To create a new materialized view:
1. Open `spark_materialized_views.json`.
2. Add a new entry following the format above.

Note: Views should only reference tables that are already ingested and available inside the Delta Lake.

## License & Copyright
Copyright (C) Environmental Data and Governance Initiative (EDGI) This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the [LICENSE](../LICENSE) file for details.