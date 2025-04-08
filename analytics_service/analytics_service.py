import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from pymongo import MongoClient, errors
import numpy as np
from mysql.connector import Error
from typing import Dict, List, Optional
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(title="Analytics API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL configuration from environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

# MongoDB configuration from environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_COLLECTION = "float_statistics"


# Function to connect to MySQL with retries
def get_mysql_connection(retries=5, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                database=MYSQL_DB,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD
            )
            if connection.is_connected():
                return connection
        except Error as e:
            attempt += 1
            print(f"MySQL connection attempt {attempt} failed: {str(e)}")
            if attempt >= retries:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"MySQL connection failed after {retries} attempts: {str(e)}"
                )
            import time
            time.sleep(delay)  # Wait before retrying


def get_mongo_connection(retries=10, delay=10):
    attempt = 0
    while attempt < retries:
        try:
            client = MongoClient(MONGO_URI)
            client.admin.command('ping')  # Test the connection
            return client
        except errors.ServerSelectionTimeoutError as e:
            attempt += 1
            print(f"MongoDB connection attempt {attempt} failed: {str(e)}")
            if attempt >= retries:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"MongoDB connection failed after {retries} attempts: {str(e)}"
                )
            import time
            time.sleep(delay)  # Wait before retrying


def get_mysql_data():
    """Fetch data from the MySQL database."""
    connection = get_mysql_connection()  # Ensure we get a valid connection
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT value FROM float_values")
        result = cursor.fetchall()  # Fetch all rows of the table
        return [row[0] for row in result]  # Return only the float values
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(err)}"
        )
    finally:
        if connection:
            connection.close()


def compute_statistics(values):
    """Compute descriptive statistics: min, max, mean, and median."""
    if not values:
        return {"min": None, "max": None, "mean": None, "median": None}

    stats = {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
    }
    return stats


def insert_to_mongodb(stats):
    """Insert statistics into MongoDB."""
    client = get_mongo_connection()  # Ensure MongoDB connection is valid
    try:
        db = client['analytics']
        collection = db[MONGO_COLLECTION]

        # Replace the existing document with the type "descriptive_statistics", ensuring it's only one document
        collection.replace_one(
            {"type": "descriptive_statistics"},  # Find document by the type
            {"type": "descriptive_statistics", **stats},  # Replace it with the new stats, keeping the same type field
            upsert=True  # If no document exists, insert it; if one exists, replace it
        )
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB error: {str(e)}"
        )
    finally:
        client.close()


def get_from_mongodb():
    """Get the latest statistics from MongoDB."""
    client = get_mongo_connection()
    try:
        db = client['analytics']
        collection = db[MONGO_COLLECTION]
        stats = collection.find_one({"type": "descriptive_statistics"})
        if stats:
            # Remove MongoDB _id and type fields
            stats.pop('_id', None)
            stats.pop('type', None)
            return stats
        else:
            return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB error: {str(e)}"
        )
    finally:
        client.close()


class FloatValue(BaseModel):
    value: float


@app.post("/insert-float/")
async def insert_float(float_data: FloatValue):
    """API endpoint to insert a float value into the MySQL database."""
    connection = get_mysql_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO float_values (value) VALUES (%s)", (float_data.value,))
        connection.commit()
        return {"value": float_data.value, "status": "success"}
    except mysql.connector.Error as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(err)}"
        )
    finally:
        if connection:
            connection.close()


@app.get("/run-analytics/")
async def run_analytics():
    """API endpoint to run analytics on demand and return the results."""
    # Fetch data from MySQL
    values = get_mysql_data()

    if not values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found in the database"
        )

    # Compute statistics
    stats = compute_statistics(values)

    # Insert stats into MongoDB
    insert_to_mongodb(stats)

    # Return the computed statistics
    return stats


@app.get("/get-stats/")
async def get_stats():
    """API endpoint to get the latest statistics from MongoDB."""
    stats = get_from_mongodb()
    if stats:
        return stats
    else:
        # If no stats exist yet, run analytics on demand
        return await run_analytics()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)