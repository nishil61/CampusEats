from db import (
    create_menu_item,
    create_vendor,
    create_user,
    get_user_by_email
)
import hashlib

def setup_initial_data():
    # Create admin user if not exists
    admin_email = "admin@campuseats.com"
    if not get_user_by_email(admin_email):
        admin_data = {
            "email": admin_email,
            "password": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "admin",
            "name": "Campus Eats Admin"
        }
        create_user(admin_data)
        print("Admin user created successfully")

    # Create sample campus vendors
    vendors = [
        {
            "name": "Campus Cafe",
            "description": "Your go-to place for quick bites and coffee",
            "address": "Main Campus Building, Ground Floor",
            "phone": "+1234567890",
            "email": "cafeteria@university.edu"
        },
        {
            "name": "Pizza Corner",
            "description": "Freshly baked pizzas and pasta",
            "address": "Student Center, Food Court",
            "phone": "+1234567891",
            "email": "pizza@university.edu"
        }
    ]

    vendor_ids = []
    for vendor in vendors:
        vendor_id = create_vendor(vendor)
        vendor_ids.append(vendor_id)
        print(f"Vendor {vendor['name']} created successfully")

    # Create sample menu items
    sample_items = [
        # Campus Cafe items
        {
            "name": "Campus Special Coffee",
            "description": "Freshly brewed coffee with a hint of cinnamon",
            "price": 3.99,
            "category": "Beverages",
            "vendor_id": vendor_ids[0],
            "image_url": "https://example.com/coffee.jpg",
            "is_available": True
        },
        {
            "name": "Student Breakfast Combo",
            "description": "Sandwich, coffee, and a fruit",
            "price": 7.99,
            "category": "Breakfast",
            "vendor_id": vendor_ids[0],
            "image_url": "https://example.com/breakfast.jpg",
            "is_available": True
        },
        # Pizza Corner items
        {
            "name": "Student Special Pizza",
            "description": "Large pizza with 3 toppings of your choice",
            "price": 12.99,
            "category": "Pizza",
            "vendor_id": vendor_ids[1],
            "image_url": "https://example.com/pizza.jpg",
            "is_available": True
        },
        {
            "name": "Pasta Bowl",
            "description": "Penne pasta with choice of sauce",
            "price": 8.99,
            "category": "Pasta",
            "vendor_id": vendor_ids[1],
            "image_url": "https://example.com/pasta.jpg",
            "is_available": True
        }
    ]

    for item in sample_items:
        create_menu_item(item)
    print("Sample menu items created successfully")

if __name__ == "__main__":
    setup_initial_data()
    print("Initial setup completed successfully") 