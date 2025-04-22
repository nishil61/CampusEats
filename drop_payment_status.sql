USE canteen1;

-- Drop payment_status column from orders table
ALTER TABLE orders
DROP COLUMN IF EXISTS payment_status; 