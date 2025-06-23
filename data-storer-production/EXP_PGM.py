from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, split, col
import os
import logging
from datetime import datetime
from delta import *
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

STORAGE_PATH = os.getenv("STORAGE_HOST_PATH")
EXTRACTED_DATA_PATH = os.path.join(STORAGE_PATH, 'updated-datasets')
JSON_PATH = os.getenv("JSON_DIR_HOST_PATH")
DELTA_LAKE_PATH = os.path.join(STORAGE_PATH, 'data-lake')
SCHEMAS_PATH = os.path.join(JSON_PATH, 'schemas')

# Initialize Spark session with Delta Lake support
# the master URL should be the environment variable (e.g., spark://app1.7077)
spark = SparkSession.builder.appName("Delta Lookup Table") \
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
        .getOrCreate()

def process_pgm(spark, pgm):
    source_table = os.path.abspath(os.path.join(DELTA_LAKE_PATH, "files", "ECHO_EXPORTER"))  # Adjust to your Delta Lake path
    target_table =  os.path.abspath(os.path.join(DELTA_LAKE_PATH, "files", "EXP_PGM"))

    logger.info(f"Processing {pgm[0]} → {pgm[1]}")

    # Read ECHO_EXPORTER Delta table
    df = spark.read.format("delta").load(source_table)
    df.createOrReplaceTempView('echo_exporter')

    # Filter records where the flag is 'Y' and REGISTRY_ID is not NULL
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW filtered_data AS 
        SELECT REGISTRY_ID, {pgm[1]} 
        FROM echo_exporter
        WHERE {pgm[0]} = 'Y' AND REGISTRY_ID IS NOT NULL
    """)

    # Split multiple IDs in the column and explode
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW exploded_data AS
        SELECT 
            '{pgm[1]}' AS PGM, 
            REGISTRY_ID, 
            EXPLODE(SPLIT({pgm[1]}, ' ')) AS PGM_ID
        FROM filtered_data
    """)
    
    # Check if the Delta table exists and create it if it doesn't
    if not DeltaTable.isDeltaTable(spark, target_table):
        logger.info(f"Creating table {target_table}...")
        # Create an empty Delta table with the schema
        schema = "PGM STRING, REGISTRY_ID STRING, PGM_ID STRING"
        spark.sql(f"CREATE TABLE IF NOT EXISTS delta.`{target_table}` ({schema}) USING DELTA")
    
    logger.info("Created Table")
    # Insert the exploded data into the Delta table (EXP_PGM)
    spark.sql(f"""
        INSERT INTO delta.`{target_table}`
        SELECT PGM, REGISTRY_ID, PGM_ID
        FROM exploded_data
    """)

    logger.info(f"Inserted records into {target_table}")

def build_exp_pgm(spark):
    target_table = os.path.join(DELTA_LAKE_PATH, "EXP_PGM")
    
    # Truncate table (overwrite)
    logger.info("Truncating EXP_PGM table...")
    # spark.sql(f"DELETE FROM delta.`{target_table}`")
    if os.path.exists(target_table) and DeltaTable.isDeltaTable(spark, target_table):
        delta_table = DeltaTable.forPath(spark, target_table)
        delta_table.delete()

    flags_and_ids = { 
        "SDWIS_FLAG": "SDWA_IDS",
        "RCRA_FLAG": "RCRA_IDS",    
        "NPDES_FLAG": "NPDES_IDS",
        "AIR_FLAG": "AIR_IDS",
        "RCRA_FLAG": "RCRA_IDS",
    }

    for pgm in flags_and_ids.items():
        process_pgm(spark, pgm)

    logger.info("Lookup table EXP_PGM updated successfully!")

# Run the script
if __name__ == "__main__":
    build_exp_pgm(spark)
