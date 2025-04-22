import mysql.connector

def modify_tables():
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Your MySQL root password here
            database="canteen"
        )
        cursor = conn.cursor()
        
        # Read and execute SQL file
        with open('modify_tables.sql', 'r') as file:
            sql_commands = file.read().split(';')
            
            for command in sql_commands:
                if command.strip():
                    cursor.execute(command)
                    print(f"Successfully executed: {command}")
        
        conn.commit()
        print("Tables modified successfully!")
        
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    modify_tables() 
 
 