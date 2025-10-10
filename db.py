import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Root",  # change to your MySQL password
            database="cqms"
        )
    except Error as e:
        print(f"Database connection error: {e}")
        return None
