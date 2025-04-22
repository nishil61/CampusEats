import mysql.connector
import streamlit as st
import os
from PIL import Image
import io

def display_vendor_menu():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        cursor = conn.cursor()
        
        # Debug: Show connection status
        st.write("Database connection successful")
        
        # Get all vendors
        cursor.execute("SELECT id, name, description FROM vendors")
        vendors = cursor.fetchall()
        
        # Debug: Show vendors count
        st.write(f"Found {len(vendors)} vendors")
        
        if not vendors:
            st.info("No vendors available at the moment.")
            return
        
        # Initialize cart in session state if not exists
        if 'cart' not in st.session_state:
            st.session_state.cart = {}
        
        # Add cart button at the top
        col1, col2 = st.columns([3, 1])
        with col2:
            cart_button = st.button("🛒 Cart")
            if cart_button:
                st.session_state.show_cart = True
        
        # Create tabs for each vendor
        vendor_tabs = st.tabs([vendor[1] for vendor in vendors])
        
        for i, (vendor_id, vendor_name, vendor_desc) in enumerate(vendors):
            with vendor_tabs[i]:
                st.subheader(vendor_name)
                st.write(vendor_desc)
                
                # Get menu items for this vendor
                cursor.execute("""
                    SELECT id, name, description, price, image_blob, available
                    FROM menu_items 
                    WHERE vendor_id = %s
                """, (vendor_id,))
                
                menu_items = cursor.fetchall()
                
                # Debug: Show menu items count for this vendor
                st.write(f"Found {len(menu_items)} items for {vendor_name}")
                
                if not menu_items:
                    st.info("No items available from this vendor.")
                    continue
                
                # Display menu items in columns
                cols = st.columns(2)
                for idx, (item_id, name, desc, price, image_blob, available) in enumerate(menu_items):
                    with cols[idx % 2]:
                        # Create a container for each item
                        with st.container():
                            # Display image if available
                            if image_blob is not None:
                                try:
                                    # Convert blob to image
                                    image = Image.open(io.BytesIO(image_blob))
                                    # Display the image
                                    st.image(
                                        image,
                                        caption=name,
                                        use_container_width=True,
                                        output_format='JPEG'
                                    )
                                except Exception as e:
                                    st.error(f"Error loading image for {name}: {str(e)}")
                                    # Debug information
                                    st.write(f"Image blob size: {len(image_blob) if image_blob else 0} bytes")
                            else:
                                st.warning(f"No image available for {name}")
                            
                            st.write(f"**{name}**")
                            if desc:
                                st.write(desc)
                            st.write(f"Price: ₹{price:.2f}")
                            
                            # Check if item is available
                            if not available:
                                st.error("⚠️ Out of Stock")
                            else:
                                # Add to cart functionality only for available items
                                quantity = st.number_input(
                                    f"Quantity for {name}",
                                    min_value=0,
                                    max_value=10,
                                    value=st.session_state.cart.get(item_id, 0),
                                    key=f"qty_{item_id}"
                                )
                                
                                # Update cart when quantity changes
                                if quantity != st.session_state.cart.get(item_id, 0):
                                    if quantity > 0:
                                        st.session_state.cart[item_id] = quantity
                                    elif item_id in st.session_state.cart:
                                        del st.session_state.cart[item_id]
                                    st.rerun()  # Rerun to update the display
        
        # Show cart summary in a popup when cart is clicked
        if st.session_state.get('show_cart', False):
            with st.container():
                st.subheader("🛒 Your Cart")
                st.subheader("Order Summary")
                
                if st.session_state.cart:
                    total = 0
                    for item_id, quantity in st.session_state.cart.items():
                        cursor.execute("""
                            SELECT name, price, available 
                            FROM menu_items 
                            WHERE id = %s
                        """, (item_id,))
                        item = cursor.fetchone()
                        if item:
                            name, price, available = item
                            if not available:
                                st.error(f"{name} is no longer available and will be removed from your cart")
                                del st.session_state.cart[item_id]
                                continue
                            st.write(f"{name} x {quantity} = ₹{price * quantity:.2f}")
                            total += price * quantity
                    st.write("---")
                    st.write(f"**Total Amount: ₹{total:.2f}**")
                    
                    # Add checkout button
                    if st.button("Proceed to Checkout"):
                        st.session_state.checkout = True
                        st.session_state.show_cart = False
                    
                    # Add close button
                    if st.button("Close Cart"):
                        st.session_state.show_cart = False
                else:
                    st.info("Your cart is empty")
                    if st.button("Close Cart"):
                        st.session_state.show_cart = False
        
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.write(f"Error details: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def get_menu_items():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.id, v.name as vendor_name, m.name, m.description, m.price, m.image_path
            FROM menu_items m
            JOIN vendors v ON m.vendor_id = v.id
            WHERE m.available = TRUE
        """)
        
        return cursor.fetchall()
        
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
        return []
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close() 