import pyspark
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, FloatType, LongType, DoubleType, BooleanType
from pyspark.sql.functions import col, to_date, trim
from delta import *
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv


# Load .env file
load_dotenv('/home/yemoeaung1/echo-pipeline/.env')
print(os.getenv("STORAGE_HOST_PATH"))

STORAGE_PATH = os.getenv("STORAGE_HOST_PATH")
JSON_PATH = os.getenv("JSON_DIR_HOST_PATH")
DELTA_LAKE_PATH = os.path.join(STORAGE_PATH, 'data-lake')
EXTRACTED_DATA_PATH = os.path.join(STORAGE_PATH, 'updated-datasets')
SCHEMAS_PATH = os.path.join(JSON_PATH, 'schemas')
MATERIALIZED_VIEW_JSON = os.path.join(JSON_PATH, 'spark_materialized_views.json')
CSV_SCHEMA_MAP_JSON = os.path.join(JSON_PATH, 'schema_csv_mapping.json')

import mview_functions
import EXP_PGM

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


data_files_to_store = os.listdir(EXTRACTED_DATA_PATH)
missed_files = []


def find_mapping(csv_filename, csv_schema_map):
    with open(csv_schema_map, 'r') as f:
        data = json.load(f)
    return data.get(csv_filename, None)


def get_schema(file_path):
    spark_dtype_mapping = {
        "IntegerType()": IntegerType(),
        "LongType()": LongType(),
        "DoubleType()": DoubleType(),
        "StringType()": StringType(),  
        "FloatType()": FloatType(),
        "ShortType()": IntegerType(),
        "BooleanType()": BooleanType(),
        "DateType()": StringType(),  # Dates will be stored as strings
        "TimestampType()": StringType()  # Timestamps will be stored as strings
    }

    schema_file_path = find_mapping(f"{file_path}.csv", csv_schema_map=CSV_SCHEMA_MAP_JSON)
    if not schema_file_path or "missing" in schema_file_path:
        logger.warning(f"Schema does not exist for {file_path}.csv.")
        return None, None
    schema_file = os.path.join(SCHEMAS_PATH, schema_file_path)


    with open(schema_file, 'r') as file:
        data = json.load(file)
        columns = data['schema']

    # Initialize an empty list to hold the schema fields
    field_list = []
    
    field_list.extend([StructField(column['COLUMN_NAME'].upper(), spark_dtype_mapping[column['SPARK_DATA_TYPE']], True) 
                      for column in columns])
    
    # Create and return the schema
    return schema_file, StructType(field_list)

def schemas_are_different(schema1, schema2):
    # Check if the number of fields are different
    if len(schema1.fields) != len(schema2.fields):
        return True

    # Compare fields and their data types
    for field1, field2 in zip(schema1.fields, schema2.fields):
        if field1.name != field2.name or field1.dataType != field2.dataType:
            return True

    # Schemas are the same
    return False

def ingest_file(file):
    logger.info(f"Processing {file}")
    filename = file.split('.')[0]
    schema_file, new_schema = get_schema(filename)
    delta_table_path = os.path.join(DELTA_LAKE_PATH, 'files', filename)
    schema_save_path = os.path.join(DELTA_LAKE_PATH, 'schemas', filename)

    if not new_schema:
        logger.warning(f"Did not find schema for {file} as it's not specified in the csv to schema mapping file. Skipping...")
        os.remove(os.path.join(EXTRACTED_DATA_PATH, file))
        return False
    
    try:
        df = spark.read.format("csv").option("header", "true").schema(new_schema).load(
            os.path.join(EXTRACTED_DATA_PATH, file))

        # Check if delta table is new
        if os.path.exists(delta_table_path) and DeltaTable.isDeltaTable(spark, delta_table_path):
            delta_table_df = DeltaTable.forPath(spark, delta_table_path).toDF()
            existing_schema = delta_table_df.schema
            
            if schemas_are_different(existing_schema, new_schema):
                logger.warning(f"Schema change detected for {filename}. Overwriting table...")
                df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(delta_table_path)

                # Store new schema
                schema_to_save = spark.read.json(schema_file, multiLine=True)
                schema_to_save.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(schema_save_path)
                logger.info(f"Schema for {filename} saved successfully.")
            else:
                logger.info(f"Schema unchanged. Writing new data to {filename}...")
                df.write.format("delta").mode("overwrite").save(delta_table_path)
                logger.info(f"New data saved to {filename} Delta Table")

        else:
            logger.info(f"Creating new Delta table for {filename}...")
            df.write.format("delta").mode("overwrite").save(delta_table_path)
            logger.info(f"Saving schema for {filename} in Delta Lake...")
            schema_to_save = spark.read.json(schema_file, multiLine=True)
            schema_to_save.write.format("delta").mode("overwrite").save(schema_save_path)
            logger.info(f"{filename} and its schema are now saved.")
        
        # Check if all rows got stored in the table
        stored_count = spark.read.format("delta").load(delta_table_path).count()
        if (df.count() != stored_count):
            logger.error(f"{file}: Row count mismatch between Delta table and CSV")
            return False
        

    except Exception as e:
        # Log the error and move to the next file
        logger.exception(f"Error processing file {file}: {str(e)}")
        return False
    
    logger.info(f"Successfully ingested {file}")
    return True


# Initialize spark
# the master URL should be the environment variable (e.g., spark://app1.7077)
builder = pyspark.sql.SparkSession.builder.appName("CSV to Delta Lake") \
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()

def main():
    os.makedirs(DELTA_LAKE_PATH, exist_ok=True)
    logger.info('Made Delta Lake folder')

    # Ingest each file to delta lake 
    ingested_files = 0
    for file in data_files_to_store:
        if not ingest_file(file):
           missed_files.append(file)
        else:
            ingested_files += 1
    
    logger.info(f"Processing completed. {ingested_files} files stored successfully.")
    if missed_files:
        logger.warning(f"{len(missed_files)} files failed: {missed_files}")
        
    # Make EXP_PGM lookup table
    logger.info("Making EXP PGM table...")
    EXP_PGM.build_exp_pgm(spark)
    
    # Create the materialized views
    missed_mview_tables = []
    successful_mview_tables = 0
    logger.info("Creating materialized view tables")
    materialized_views_to_make = json.load(open(MATERIALIZED_VIEW_JSON, "r"))
    for key, entry in materialized_views_to_make.items():
        logger.info(f"Making {key} materialized view")
        if not mview_functions.create_mview(spark, key, entry):
            missed_mview_tables.append(key)
        else:
            successful_mview_tables += 1
        
        # Unload views from memory
        views = spark.sql("SHOW VIEWS").collect()
        for row in views:
            view_name = row["viewName"]
            
            # Drop all view except the two
            if view_name not in ["EXP_PGM", "ECHO_EXPORTER"]:
                spark.sql(f"DROP VIEW IF EXISTS {view_name}")
        
    logger.info(f"Completed creating materialized views. {successful_mview_tables} materialized views created.")
    if missed_mview_tables:
        logger.warning(f"{len(missed_mview_tables)} tables failed to be created: {missed_mview_tables}")
    
    spark.stop()


if __name__ == '__main__':
    main()