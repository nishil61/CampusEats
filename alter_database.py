import mysql.connector
from db import get_connection

def alter_database():
    try:
        # Read SQL file
        with open('alter_tables.sql', 'r') as file:
            sql_commands = file.read().split(';')
        
        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Your MySQL root password here
            database="canteen"
        )
        cursor = conn.cursor()
        
        # Execute each SQL command
        for command in sql_commands:
            if command.strip():
                try:
                    cursor.execute(command)
                    print(f"Successfully executed: {command[:50]}...")
                except mysql.connector.Error as e:
                    print(f"Error executing command: {command[:50]}...")
                    print(f"Error details: {e}")
        
        conn.commit()
        print("Database tables altered successfully!")
        
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    alter_database() 
 
 