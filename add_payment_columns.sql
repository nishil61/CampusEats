USE canteen1;

-- Add payment related columns to orders table if they don't exist
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS payment_id VARCHAR(255) AFTER status,
ADD COLUMN IF NOT EXISTS razorpay_order_id VARCHAR(255) AFTER payment_id; 