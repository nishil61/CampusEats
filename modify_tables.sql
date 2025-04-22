USE canteen;

-- Drop existing foreign key constraints
ALTER TABLE order_items DROP FOREIGN KEY IF EXISTS order_items_ibfk_1;
ALTER TABLE order_items DROP FOREIGN KEY IF EXISTS order_items_ibfk_2;

-- Drop existing tables
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;

-- Recreate orders table with auto-increment
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'preparing', 'ready', 'delivered') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recreate order_items table with proper foreign keys
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    menu_item_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_time DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
);

-- Add name column to users table
ALTER TABLE users ADD COLUMN name VARCHAR(255) AFTER id;

-- Add price_at_time column to order_items table
ALTER TABLE order_items ADD COLUMN price_at_time DECIMAL(10,2) NOT NULL AFTER quantity; 
 
 