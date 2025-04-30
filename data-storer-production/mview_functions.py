import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

DELTA_LAKE_PATH = os.getenv("DELTA_LAKE_PATH")

def load_table(spark, name):
    df = spark.read.format("delta").load(os.path.join(DELTA_LAKE_PATH, 'files', name))
    cleaned_name = name.replace("-", "_")
    df.createOrReplaceTempView(cleaned_name)
    return cleaned_name

def create_mview(spark, view, entry):
    # Loading each delta table to memory to be used with sql 
    for table in entry['tables']:
        try:
            logger.info(f'Loading {table} as a view.')
            load_table(spark, table)
        except Exception as e:
            logger.exception(f"Error loading table {table} as view. Error: {e}")
            return False
    
    logger.info(f"Loaded tables used to create {view} materialized view.")

    # Running each query statement needed to make the table
    for statement in entry['statements']:
        try:
            # Dynamically append table path if statement is creating table
            if "CREATE OR REPLACE TEMP VIEW" not in statement:
                sql =  f"CREATE OR REPLACE TABLE delta.`{os.path.join(DELTA_LAKE_PATH, 'files', view)}` USING DELTA AS " + statement
            else:
                sql = statement
            spark.sql(sql)
            
        except Exception as e:
            print(statement)
            logger.exception(f"Skipping {view} due to error: {e}")
            return False
    
    # Check if data got lost while table was being made
    logger.info(f"{view} finished storing as delta table. Checking now to see if data exists")
    load_table(spark, view)
    row_count = spark.sql(f"SELECT * FROM {view}").count()
    if row_count == 0:
        logger.warning(f"{view} has no data stored in it. Should check why.")
        return False
    logger.info(f"{view} has {row_count} rows stored.")
    logger.info(f"{view} created as materialized view successfully.")
    return True