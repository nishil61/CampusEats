import mysql.connector

def update_schema():
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        cursor = conn.cursor()
        
        # Read and execute SQL file
        with open('alter_schema.sql', 'r') as file:
            sql_commands = file.read().split(';')
            
            for command in sql_commands:
                if command.strip():
                    try:
                        cursor.execute(command)
                        print(f"Successfully executed: {command[:50]}...")
                    except mysql.connector.Error as e:
                        print(f"Error executing command: {command[:50]}...")
                        print(f"Error details: {e}")
        
        conn.commit()
        print("Database schema updated successfully!")
        
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_schema() 
 
 