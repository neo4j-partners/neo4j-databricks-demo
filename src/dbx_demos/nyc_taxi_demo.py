"""
NYC Taxi Data Demo

This script loads and displays the classic Databricks NYC taxi dataset.
"""



def main():

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




if __name__ == "__main__":
    main()
