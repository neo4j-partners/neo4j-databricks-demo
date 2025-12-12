"""
NYC Taxi Data Demo

This script loads and displays the classic Databricks NYC taxi dataset.
"""

from pyspark.sql import SparkSession


def main():
    # Create Spark session
    spark = SparkSession.builder.appName("NYC Taxi Demo").getOrCreate()

    # Load the NYC taxi dataset from Databricks sample datasets
    df = spark.read.format("delta").load(
        "/databricks-datasets/nyctaxi/tables/nyctaxi_yellow"
    )

    # Print schema to understand the data structure
    print("Schema:")
    df.printSchema()

    # Print first 10 rows
    print("\nFirst 10 rows:")
    df.show(10)

    # Stop the Spark session
    spark.stop()


if __name__ == "__main__":
    main()
