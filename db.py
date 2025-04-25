from pymongo import MongoClient
from pymongo.errors import ConnectionError, OperationFailure
import streamlit as st
from config import (
    MONGODB_URI, DB_NAME,
    USERS_COLLECTION, MENU_ITEMS_COLLECTION,
    ORDERS_COLLECTION, ORDER_ITEMS_COLLECTION,
    VENDORS_COLLECTION
)
from bson import ObjectId

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
except ConnectionError as e:
    st.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

# Collections
users = db[USERS_COLLECTION]
orders = db[ORDERS_COLLECTION]
menu_items = db[MENU_ITEMS_COLLECTION]
order_items = db[ORDER_ITEMS_COLLECTION]
vendors = db[VENDORS_COLLECTION]

def get_user_by_email(email):
    """Get user by email"""
    try:
        return users.find_one({"email": email})
    except OperationFailure as e:
        st.error(f"Database operation failed: {str(e)}")
        return None

def create_user(user_data):
    """Create a new user"""
    try:
        result = users.insert_one(user_data)
        return result.inserted_id
    except OperationFailure as e:
        st.error(f"Failed to create user: {str(e)}")
        return None

def create_order(order_data):
    """Create a new order"""
    try:
        result = orders.insert_one(order_data)
        return result.inserted_id
    except OperationFailure as e:
        st.error(f"Failed to create order: {str(e)}")
        return None

def get_order_by_id(order_id):
    """Get order by ID"""
    try:
        if isinstance(order_id, str):
            order_id = ObjectId(order_id)
        return orders.find_one({"_id": order_id})
    except OperationFailure as e:
        st.error(f"Failed to get order: {str(e)}")
        return None

def update_order_status(order_id, status):
    """Update order status"""
    try:
        if isinstance(order_id, str):
            order_id = ObjectId(order_id)
        result = orders.update_one(
            {"_id": order_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    except OperationFailure as e:
        st.error(f"Failed to update order status: {str(e)}")
        return False

def get_menu_items(category=None, vendor_id=None):
    """Get menu items with optional filtering"""
    try:
        query = {}
        if category:
            query["category"] = category
        if vendor_id:
            query["vendor_id"] = vendor_id
        return list(menu_items.find(query))
    except OperationFailure as e:
        st.error(f"Failed to get menu items: {str(e)}")
        return []

def get_user_orders(user_id):
    """Get all orders for a user"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return list(orders.find({"user_id": user_id}).sort("created_at", -1))
    except OperationFailure as e:
        st.error(f"Failed to get user orders: {str(e)}")
        return []

def get_all_orders(status=None):
    """Get all orders with optional status filter"""
    try:
        query = {}
        if status:
            query["status"] = status
        return list(orders.find(query).sort("created_at", -1))
    except OperationFailure as e:
        st.error(f"Failed to get all orders: {str(e)}")
        return []

def create_menu_item(item_data):
    """Create a new menu item"""
    try:
        result = menu_items.insert_one(item_data)
        return result.inserted_id
    except OperationFailure as e:
        st.error(f"Failed to create menu item: {str(e)}")
        return None

def update_menu_item(item_id, update_data):
    """Update a menu item"""
    try:
        if isinstance(item_id, str):
            item_id = ObjectId(item_id)
        result = menu_items.update_one(
            {"_id": item_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except OperationFailure as e:
        st.error(f"Failed to update menu item: {str(e)}")
        return False

def delete_menu_item(item_id):
    """Delete a menu item"""
    try:
        if isinstance(item_id, str):
            item_id = ObjectId(item_id)
        result = menu_items.delete_one({"_id": item_id})
        return result.deleted_count > 0
    except OperationFailure as e:
        st.error(f"Failed to delete menu item: {str(e)}")
        return False

def create_vendor(vendor_data):
    """Create a new vendor"""
    try:
        result = vendors.insert_one(vendor_data)
        return result.inserted_id
    except OperationFailure as e:
        st.error(f"Failed to create vendor: {str(e)}")
        return None

def get_vendor_by_id(vendor_id):
    """Get vendor by ID"""
    try:
        if isinstance(vendor_id, str):
            vendor_id = ObjectId(vendor_id)
        return vendors.find_one({"_id": vendor_id})
    except OperationFailure as e:
        st.error(f"Failed to get vendor: {str(e)}")
            return None
            
def get_all_vendors():
    """Get all vendors"""
    try:
        return list(vendors.find())
    except OperationFailure as e:
        st.error(f"Failed to get vendors: {str(e)}")
        return []

def update_payment_status(order_id, payment_status, payment_id=None):
    """Update payment status for an order"""
    try:
        if isinstance(order_id, str):
            order_id = ObjectId(order_id)
        update_data = {"payment_status": payment_status}
        if payment_id:
            update_data["payment_id"] = payment_id
        result = orders.update_one(
            {"_id": order_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except OperationFailure as e:
        st.error(f"Failed to update payment status: {str(e)}")
        return False

def get_collection(collection_name):
    """Get a MongoDB collection"""
    return db[collection_name]

def insert_one(collection_name, document):
    """Insert a single document into a collection"""
    try:
        collection = get_collection(collection_name)
        result = collection.insert_one(document)
        return result.inserted_id
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def find_one(collection_name, query):
    """Find a single document in a collection"""
    try:
        collection = get_collection(collection_name)
        return collection.find_one(query)
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None
        
def find(collection_name, query=None):
    """Find multiple documents in a collection"""
    try:
        collection = get_collection(collection_name)
        if query is None:
            return list(collection.find())
        return list(collection.find(query))
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []

def update_one(collection_name, query, update_data):
    """Update a single document in a collection"""
    try:
        collection = get_collection(collection_name)
        result = collection.update_one(query, {"$set": update_data})
        return result.modified_count > 0
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False

def delete_one(collection_name, query):
    """Delete a single document from a collection"""
    try:
        collection = get_collection(collection_name)
        result = collection.delete_one(query)
        return result.deleted_count > 0
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False
