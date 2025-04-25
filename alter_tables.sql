USE canteen;

-- Alter users table to add name column if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS name VARCHAR(255) AFTER password;

-- Modify role enum in users table
ALTER TABLE users 
MODIFY COLUMN role ENUM('admin', 'client') NOT NULL;

-- Add category to menu_items if it doesn't exist
ALTER TABLE menu_items 
ADD COLUMN IF NOT EXISTS category VARCHAR(100) AFTER price;

-- Modify status enum in orders table
ALTER TABLE orders 
MODIFY COLUMN status ENUM('pending', 'preparing', 'ready', 'delivered') DEFAULT 'pending';

-- Add price_at_time to order_items if it doesn't exist
ALTER TABLE order_items 
ADD COLUMN IF NOT EXISTS price_at_time DECIMAL(10,2) NOT NULL AFTER quantity; 
 
 
 