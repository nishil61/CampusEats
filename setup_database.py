import mysql.connector
from db import get_connection

def setup_database():
    try:
        # Read SQL file
        with open('setup_database.sql', 'r') as file:
            sql_commands = file.read().split(';')
        
        # Connect to MySQL (without database)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""  # Your MySQL root password here
        )
        cursor = conn.cursor()
        
        # Execute each SQL command
        for command in sql_commands:
            if command.strip():
                cursor.execute(command)
        
        conn.commit()
        print("Database and tables created successfully!")
        
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_database() 
 
 
 