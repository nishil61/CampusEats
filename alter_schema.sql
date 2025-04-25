USE canteen1;

-- Add payment status and related columns to orders table
ALTER TABLE orders
ADD COLUMN payment_status ENUM('pending', 'completed', 'failed') NOT NULL DEFAULT 'pending' AFTER status,
ADD COLUMN payment_id VARCHAR(255) AFTER payment_status,
ADD COLUMN razorpay_order_id VARCHAR(255) AFTER payment_id;

-- Add price_at_time column to order_items table
ALTER TABLE order_items
ADD COLUMN price_at_time DECIMAL(10,2) NOT NULL AFTER quantity;

-- Update existing orders to have default payment status
UPDATE orders SET payment_status = 'pending' WHERE payment_status IS NULL;

-- Update existing order_items to have price_at_time
UPDATE order_items oi
JOIN menu_items mi ON oi.menu_item_id = mi.id
SET oi.price_at_time = mi.price
WHERE oi.price_at_time IS NULL; 
 
 
 