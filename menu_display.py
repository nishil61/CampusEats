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
        
        # Get all vendors
        cursor.execute("SELECT id, name, description FROM vendors")
        vendors = cursor.fetchall()
        
        if not vendors:
            st.info("No vendors available at the moment.")
            return
        
        # Initialize cart in session state if not exists
        if 'cart' not in st.session_state:
            st.session_state.cart = {}
        
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
        
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
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