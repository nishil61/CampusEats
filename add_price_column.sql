USE canteen;

-- Add price_at_time column to order_items table if it doesn't exist
ALTER TABLE order_items 
ADD COLUMN IF NOT EXISTS price_at_time DECIMAL(10,2) NOT NULL DEFAULT 0.00 AFTER quantity; 
 
 