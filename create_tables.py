import mysql.connector
from config import DB_CONFIG

def create_tables():
    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        db_executor = conn.cursor()
        
        # Create users table if not exists
        db_executor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role ENUM('user', 'vendor', 'admin') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create vendors table if not exists
        db_executor.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create menu_items table if not exists
        db_executor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vendor_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                image_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(id)
            )
        """)
        
        # Create orders table if not exists
        db_executor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                status ENUM('pending', 'completed', 'cancelled') NOT NULL,
                razorpay_order_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create order_items table if not exists
        db_executor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                menu_item_id INT NOT NULL,
                quantity INT NOT NULL,
                price_at_time DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
            )
        """)
        
        # Create vendor_order_status table if not exists
        db_executor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_order_status (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                vendor_id INT NOT NULL,
                status ENUM('pending', 'accepted', 'rejected', 'completed') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (vendor_id) REFERENCES vendors(id)
            )
        """)
        
        # Create payments table if not exists
        db_executor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                status ENUM('pending', 'completed', 'failed') NOT NULL,
                razorpay_payment_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        """)
        
        conn.commit()
        print("Successfully created all required tables")
        
    except mysql.connector.Error as e:
        print(f"Error creating tables: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'db_executor' in locals():
            db_executor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_tables() 