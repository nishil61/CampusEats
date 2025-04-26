import mysql.connector
from config import DB_CONFIG

def create_vendor_status_table():
    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        db_executor = conn.cursor()
        
        # Create vendor_order_status table
        db_executor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_order_status (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                vendor_id INT NOT NULL,
                status ENUM('pending', 'ready', 'pickedup') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (vendor_id) REFERENCES vendors(id),
                UNIQUE KEY unique_order_vendor (order_id, vendor_id)
            )
        """)
        
        conn.commit()
        print("Vendor order status table created successfully!")
        
    except mysql.connector.Error as e:
        print(f"Error creating vendor order status table: {e}")
    finally:
        if 'db_executor' in locals():
            db_executor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_vendor_status_table() 