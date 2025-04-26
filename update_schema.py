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
        db_executor = conn.cursor()
        
        # Add any new columns or modify existing ones
        commands = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE vendor_order_status ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ]
        
        for command in commands:
            db_executor.execute(command)
        
        conn.commit()
        print("Schema updated successfully!")
    except mysql.connector.Error as e:
        print(f"Error updating schema: {e}")
    finally:
        if 'db_executor' in locals():
            db_executor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_schema() 
 
 
 