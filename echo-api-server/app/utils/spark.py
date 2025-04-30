from pyspark.sql import SparkSession
from deltalake import DeltaTable, write_deltalake
from delta import *

spark_session_cache = {}

# Configure Delta Lake with Spark
def get_spark_session():
    if "spark" not in spark_session_cache:
        builder = SparkSession.builder \
                .appName("DeltaLakeQuery") \
                .master("local[*]") \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                .config("spark.driver.memory", "8g")
        spark_session_cache["spark"] = configure_spark_with_delta_pip(builder).getOrCreate()
    return spark_session_cache["spark"]