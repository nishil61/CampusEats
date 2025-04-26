# ui.py

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from db import execute_query
from auth import get_current_user
import time
import mysql.connector
from menu_display import display_vendor_menu, get_menu_items
from payment import initiate_payment, verify_payment
import os
from components.razorpay_button import razorpay_button
from config import DB_CONFIG

# ---------- Customer UI ----------
def customer_ui():
    st.header("🍔 Menu")

    # Poll every 5 s to pick up status changes
    st_autorefresh(interval=5_000, limit=None, key="cust_poll")

    # get current user
    user = get_current_user()
    if not user:
        st.error("Please log in again.")
        return

    # --- Browse & Cart as before ---
    menu = execute_query("SELECT * FROM menu_items WHERE available = TRUE", fetch=True)
    cart = st.session_state.setdefault("cart", {})

    for item in menu:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{item['name']}** – {item['description']} ($ {item['price']})")
        with c2:
            qty = st.number_input(f"Qty_{item['id']}", min_value=0, value=cart.get(item['id'], 0))
            if qty > 0:
                cart[item['id']] = qty
            elif item['id'] in cart:
                del cart[item['id']]

    if st.button("🛒 Place Order"):
        if not cart:
            st.error("Cart is empty.")
        else:
            total = sum(item["price"] * cart[item["id"]] for item in menu if item["id"] in cart)
            execute_query("INSERT INTO orders (user_id, total) VALUES (%s, %s)", (user["id"], total))
            order_id = execute_query("SELECT LAST_INSERT_ID() AS id", fetch=True)[0]["id"]
            for item_id, qty in cart.items():
                execute_query(
                    "INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_time) VALUES (%s, %s, %s, %s)",
                    (order_id, item_id, qty, next(item["price"] for item in menu if item["id"] == item_id))
                )
            st.session_state.cart = {}
            st.success("Order placed successfully!")

    # --- Show live‑updating recent orders ---
    st.markdown("---")
    st.subheader("📦 Your Recent Orders")
    orders = execute_query(
        "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
        (user["id"],),
        fetch=True
    )
    status_map = {
        "inmaking": "👩‍🍳 In making",
        "ready":    "🔔 Ready for pick‑up",
        "pickedup": "✅ Picked up"
    }
    for o in orders:
        st.info(f"Order #{o['id']} – {status_map[o['status']]}")



# ---------- Vendor UI ----------
def vendor_ui():
    st.title("Vendor Dashboard")
    
    # Get current user
    user = get_current_user()
    if not user or user["role"] != "vendor":
        st.error("Please login as a vendor to access this page.")
        return
    
    # Get vendor's name from email
    vendor_emails = {
        "feefafoo@campuseats.com": "Fee Fa Foo",
        "mechcafe@campuseats.com": "Mech Cafe",
        "poornima@campuseats.com": "Poornima Kitchen",
        "nescafe@campuseats.com": "Nescafe"
    }
    vendor_name = vendor_emails.get(user["email"])
    
    if not vendor_name:
        st.error("Invalid vendor account.")
        return
    
    # Add tabs to sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Navigation")
    selected_tab = st.sidebar.radio(
        "Go to",
        ["Orders", "Menu Management"],
        key="vendor_navigation_tabs",
        label_visibility="collapsed"
    )
    
    if selected_tab == "Orders":
        st.header(f"{vendor_name} Orders")
        try:
            # Connect to database
            conn = mysql.connector.connect(**DB_CONFIG)
            db_executor = conn.cursor()
            
            # Get vendor's ID
            db_executor.execute("SELECT id FROM vendors WHERE name = %s", (vendor_name,))
            vendor_id = db_executor.fetchone()[0]
            
            # Get orders for this vendor only
            db_executor.execute("""
                SELECT 
                    o.id,
                    o.user_id,
                    o.total,
                    o.status,
                    o.razorpay_order_id,
                    o.created_at,
                    u.email,
                    m.name as item_name,
                    oi.quantity,
                    oi.price_at_time,
                    v.name as vendor_name,
                    vos.status as vendor_status
                FROM orders o
                JOIN users u ON o.user_id = u.id
                JOIN order_items oi ON o.id = oi.order_id
                JOIN menu_items m ON oi.menu_item_id = m.id
                JOIN vendors v ON m.vendor_id = v.id
                LEFT JOIN vendor_order_status vos ON o.id = vos.order_id AND v.id = vos.vendor_id
                WHERE m.vendor_id = %s
                ORDER BY o.created_at DESC
            """, (vendor_id,))
            
            orders = db_executor.fetchall()
            
            if not orders:
                st.info("No orders found.")
                return
            
            # Group orders by order_id
            current_order = None
            items = []
            
            for order in orders:
                if current_order != order[0]:  # New order
                    if current_order is not None:  # If not first order, display previous order's items and buttons
                        # Display all items
                        for item in items:
                            st.write(f"₹{item[9]:.2f} x {item[8]} (₹{item[9] * item[8]:.2f}) {item[7]} from {item[10]}")
                        
                        # Add status update buttons after all items
                        st.write("---")  # Add separator before buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"Mark Ready #{current_order}", key=f"ready_{current_order}"):
                                # Update vendor-specific status
                                db_executor.execute("""
                                    INSERT INTO vendor_order_status (order_id, vendor_id, status)
                                    VALUES (%s, %s, 'ready')
                                    ON DUPLICATE KEY UPDATE status = 'ready'
                                """, (current_order, vendor_id))
                                
                                # Check if all vendors have marked as ready
                                db_executor.execute("""
                                    SELECT COUNT(DISTINCT m.vendor_id) as total_vendors,
                                           COUNT(DISTINCT vos.vendor_id) as ready_vendors
                                    FROM order_items oi
                                    JOIN menu_items m ON oi.menu_item_id = m.id
                                    LEFT JOIN vendor_order_status vos ON oi.order_id = vos.order_id AND m.vendor_id = vos.vendor_id AND vos.status = 'ready'
                                    WHERE oi.order_id = %s
                                """, (current_order,))
                                
                                result = db_executor.fetchone()
                                if result[0] == result[1]:  # All vendors are ready
                                    db_executor.execute(
                                        "UPDATE orders SET status = 'ready' WHERE id = %s",
                                        (current_order,)
                                    )
                                
                                conn.commit()
                                st.rerun()
                        
                        with col2:
                            if st.button(f"Mark Picked Up #{current_order}", key=f"pickedup_{current_order}"):
                                # Update vendor-specific status
                                db_executor.execute("""
                                    INSERT INTO vendor_order_status (order_id, vendor_id, status)
                                    VALUES (%s, %s, 'pickedup')
                                    ON DUPLICATE KEY UPDATE status = 'pickedup'
                                """, (current_order, vendor_id))
                                
                                # Check if all vendors have marked as picked up
                                db_executor.execute("""
                                    SELECT COUNT(DISTINCT m.vendor_id) as total_vendors,
                                           COUNT(DISTINCT vos.vendor_id) as pickedup_vendors
                                    FROM order_items oi
                                    JOIN menu_items m ON oi.menu_item_id = m.id
                                    LEFT JOIN vendor_order_status vos ON oi.order_id = vos.order_id AND m.vendor_id = vos.vendor_id AND vos.status = 'pickedup'
                                    WHERE oi.order_id = %s
                                """, (current_order,))
                                
                                result = db_executor.fetchone()
                                if result[0] == result[1]:  # All vendors are picked up
                                    db_executor.execute(
                                        "UPDATE orders SET status = 'pickedup' WHERE id = %s",
                                        (current_order,)
                                    )
                                
                                conn.commit()
                                st.rerun()
                        
                        with col3:
                            # Add View Invoice button if Razorpay order exists
                            if order[4]:  # razorpay_order_id
                                # First check in session state
                                if 'invoices' in st.session_state and str(current_order) in st.session_state.invoices:
                                    invoice_url = st.session_state.invoices[str(current_order)]
                                    st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
                                else:
                                    # If not in session state, try to fetch from Razorpay
                                    try:
                                        from payment import client
                                        invoices = client.invoice.all()
                                        for invoice in invoices['items']:
                                            if invoice['notes'].get('order_id') == str(current_order):
                                                invoice_url = invoice['short_url']
                                                st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
                                                # Store in session state for future
                                                if 'invoices' not in st.session_state:
                                                    st.session_state.invoices = {}
                                                st.session_state.invoices[str(current_order)] = invoice_url
                                                break
                                        else:
                                            st.write("Invoice not found")
                                    except Exception as e:
                                        st.error(f"Error fetching invoice: {str(e)}")
                        
                        st.write("---")  # Add separator between orders
                        items = []  # Clear items for next order
                    
                    current_order = order[0]
                    st.subheader(f"Order #{order[0]}")
                    st.write(f"Customer: {order[6]}")  # user email
                    st.write(f"Status: {order[11] or 'pending'}")  # vendor-specific status
                    st.write(f"Total: ₹{order[2]:.2f}")
                    order_date = order[5].strftime("%Y-%m-%d %H:%M:%S")
                    st.write(f"Date: {order_date}")
                    st.write("Items:")
                
                # Add item to current order's items
                items.append(order)
            
            # Display last order's items and buttons
            if items:
                for item in items:
                    st.write(f"₹{item[9]:.2f} x {item[8]} (₹{item[9] * item[8]:.2f}) {item[7]} from {item[10]}")
                
                st.write("---")  # Add separator before buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Mark Ready #{current_order}", key=f"ready_{current_order}_last"):
                        db_executor.execute(
                            "UPDATE orders SET status = 'ready' WHERE id = %s",
                            (current_order,)
                        )
                        conn.commit()
                        st.rerun()
                with col2:
                    if st.button(f"Mark Picked Up #{current_order}", key=f"pickedup_{current_order}_last"):
                        db_executor.execute(
                            "UPDATE orders SET status = 'pickedup' WHERE id = %s",
                            (current_order,)
                        )
                        conn.commit()
                        st.rerun()
                with col3:
                    # Add View Invoice button if Razorpay order exists
                    if order[4]:  # razorpay_order_id
                        # First check in session state
                        if 'invoices' in st.session_state and str(current_order) in st.session_state.invoices:
                            invoice_url = st.session_state.invoices[str(current_order)]
                            st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
                        else:
                            # If not in session state, try to fetch from Razorpay
                            try:
                                from payment import client
                                invoices = client.invoice.all()
                                for invoice in invoices['items']:
                                    if invoice['notes'].get('order_id') == str(current_order):
                                        invoice_url = invoice['short_url']
                                        st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
                                        # Store in session state for future
                                        if 'invoices' not in st.session_state:
                                            st.session_state.invoices = {}
                                        st.session_state.invoices[str(current_order)] = invoice_url
                                        break
                                else:
                                    st.write("Invoice not found")
                            except Exception as e:
                                st.error(f"Error fetching invoice: {str(e)}")
        
        except mysql.connector.Error as e:
            st.error(f"Database error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            if 'db_executor' in locals():
                db_executor.close()
            if 'conn' in locals():
                conn.close()
    
    elif selected_tab == "Menu Management":
        st.header(f"{vendor_name} Menu Management")
        try:
            # Connect to database
            conn = mysql.connector.connect(**DB_CONFIG)
            db_executor = conn.cursor()
            
            # Get vendor's ID
            db_executor.execute("SELECT id FROM vendors WHERE name = %s", (vendor_name,))
            vendor_id = db_executor.fetchone()[0]
            
            # Get menu items for this vendor
            db_executor.execute("""
                SELECT id, name, description, price, available, image_path 
                FROM menu_items 
                WHERE vendor_id = %s
                ORDER BY name
            """, (vendor_id,))
            
            menu_items = db_executor.fetchall()
            
            if menu_items:
                # Create a form for batch updates
                with st.form(f"menu_items_{vendor_id}"):
                    st.write("Update item availability:")
                    
                    # Store changes to apply them all at once
                    changes = {}
                    
                    # Create a container for menu items
                    for item in menu_items:
                        item_id, name, desc, price, available, image_path = item
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"**{name}**")
                            st.write(f"Price: ₹{price:.2f}")
                            if desc:
                                st.write(f"*{desc}*")
                        
                        with col2:
                            # Checkbox for availability
                            new_status = st.checkbox(
                                "Available",
                                value=available,
                                key=f"available_{item_id}"
                            )
                            if new_status != available:
                                changes[item_id] = new_status
                        
                        with col3:
                            st.write("Status:")
                            if available:
                                st.success("In Stock")
                            else:
                                st.error("Out of Stock")
                        
                        st.write("---")
                    
                    # Submit button for the form
                    submitted = st.form_submit_button("Save Changes")
                    if submitted:
                        try:
                            for item_id, new_status in changes.items():
                                db_executor.execute("""
                                    UPDATE menu_items 
                                    SET available = %s 
                                    WHERE id = %s
                                """, (new_status, item_id))
                            
                            conn.commit()
                            st.success("Menu items updated successfully!")
                            st.rerun()
                        except mysql.connector.Error as e:
                            st.error(f"Error updating menu items: {e}")
                            conn.rollback()
            else:
                st.info("No menu items found.")
            
            # Add new menu item section
            st.markdown("---")
            st.subheader("Add New Menu Item")
            
            # Create form for new menu item
            with st.form("add_menu_item"):
                # Item details
                name = st.text_input("Item Name")
                description = st.text_area("Description")
                price = st.number_input("Price", min_value=0.0, step=0.01)
                available = st.checkbox("Available", value=True)
                
                # Image path input
                image_path = st.text_input("Image Path (e.g., images/item_name.jpg)")
                st.info("Note: Please ensure the image file exists in the specified path before adding the item.")
                
                # Submit button
                submitted = st.form_submit_button("Add Menu Item")
                if submitted:
                    if name and description and price > 0:
                        try:
                            db_executor.execute("""
                                INSERT INTO menu_items 
                                (vendor_id, name, description, price, available, image_path)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (vendor_id, name, description, price, available, image_path or None))
                            
                            conn.commit()
                            st.success(f"Successfully added {name} to the menu!")
                            st.rerun()
                        except mysql.connector.Error as e:
                            st.error(f"Error adding menu item: {e}")
                    else:
                        st.error("Please fill in all required fields (Name, Description, and Price)")
        
        except mysql.connector.Error as e:
            st.error(f"Database error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            if 'db_executor' in locals():
                db_executor.close()
            if 'conn' in locals():
                conn.close()

def client_ui():
    st.title("🍽️ Food Ordering System")
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.error("Please login to access the menu.")
        return
    
    # Create sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["View Menu", "Cart", "My Orders"]
    )
    
    if page == "View Menu":
        display_vendor_menu()
    
    elif page == "Cart":
        cart_ui()
    
    elif page == "My Orders":
        view_my_orders_ui()
    
    # Add footer with team credits
    st.markdown("""
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 10px 0;
        text-align: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 14px;
        border-top: 1px solid #ddd;
        z-index: 999;
    }
    .footer span {
        color: #666;
        font-style: italic;
    }
    .footer strong {
        color: #333;
    }
    </style>
    <div class="footer">
        <span>Made with ❤️ by</span> <strong>Nishil, Krutagna, Jenish and Khushi</strong>
    </div>
    """, unsafe_allow_html=True)

def cart_ui():
    st.title("🛒 Your Cart")
    
    if 'cart' not in st.session_state or not st.session_state.cart:
        st.info("Your cart is empty. Please add items from the menu.")
        return
    
    # Display cart items
    st.subheader("Order Summary")
    total = 0
    
    try:
        # Use the config for database connection
        conn = mysql.connector.connect(**DB_CONFIG)
        db_executor = conn.cursor()
        
        for item_id, quantity in st.session_state.cart.items():
            # Get item details from database
            db_executor.execute("""
                SELECT m.name, m.price, v.name as vendor_name
                FROM menu_items m
                JOIN vendors v ON m.vendor_id = v.id
                WHERE m.id = %s
            """, (item_id,))
            
            item = db_executor.fetchone()
            if item:
                name, price, vendor = item
                item_total = price * quantity
                total += item_total
                st.write(f"{name} (from {vendor}) x {quantity} = ₹{item_total:.2f}")
        
        st.write("---")
        st.write(f"**Total Amount: ₹{total:.2f}**")
        
        if st.button("Place Order"):
            # Create order
            db_executor.execute(
                "INSERT INTO orders (user_id, total, status) VALUES (%s, %s, 'inmaking')",
                (st.session_state.user['id'], total)
            )
            
            order_id = db_executor.lastrowid
            
            # Add order items
            for item_id, quantity in st.session_state.cart.items():
                db_executor.execute("""
                    SELECT price FROM menu_items WHERE id = %s
                """, (item_id,))
                price = db_executor.fetchone()[0]
                
                db_executor.execute(
                    "INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_time) VALUES (%s, %s, %s, %s)",
                    (order_id, item_id, quantity, price)
                )
            
            conn.commit()
            
            # Display payment section
            st.write("### Payment")
            st.info("Please wait while we redirect you to the payment gateway...")
            
            # Initiate payment and get Razorpay order ID
            razorpay_order_id = initiate_payment(total, order_id)
            if razorpay_order_id:
                # Update order with Razorpay order ID
                db_executor.execute(
                    "UPDATE orders SET razorpay_order_id = %s WHERE id = %s",
                    (razorpay_order_id, order_id)
                )
                conn.commit()
                
                # Clear cart
                st.session_state.cart = {}
                
                # Add payment status checker with Streamlit notifications
                st.markdown(f"""
                <script>
                function checkPaymentStatus() {{
                    fetch('/check_payment_status?order_id={order_id}')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.status === 'paid') {{
                                // Show success message
                                const successDiv = document.createElement('div');
                                successDiv.innerHTML = `
                                    <div style='text-align: center; padding: 20px; background-color: #4CAF50; color: white; border-radius: 5px; margin: 20px 0;'>
                                        <h3 style='margin: 0;'>🎉 Payment Successful!</h3>
                                        <p style='margin: 10px 0; font-size: 16px;'>Your order is being prepared.</p>
                                    </div>
                                `;
                                document.body.appendChild(successDiv);
                                
                                // Show balloons
                                window.parent.postMessage({{type: 'streamlit:balloons'}}, '*');
                                
                                // Redirect after 3 seconds
                                setTimeout(() => {{
                                    window.location.href = '/my_orders';
                                }}, 3000);
                            }}
                        }});
                }}
                
                // Check payment status every 5 seconds
                setInterval(checkPaymentStatus, 5000);
                </script>
                """, unsafe_allow_html=True)
        
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'db_executor' in locals():
            db_executor.close()
        if 'conn' in locals():
            conn.close()

def view_my_orders_ui():
    st.title("My Orders")
    
    try:
        # Use the config for database connection
        conn = mysql.connector.connect(**DB_CONFIG)
        db_executor = conn.cursor()
        
        # Get user's orders with vendor information and status
        db_executor.execute("""
            SELECT o.id, o.status, o.total, o.created_at, o.razorpay_order_id,
                   v.name as vendor_name, m.name as item_name, 
                   oi.quantity, oi.price_at_time,
                   vos.status as vendor_status
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items m ON oi.menu_item_id = m.id
            JOIN vendors v ON m.vendor_id = v.id
            LEFT JOIN vendor_order_status vos ON o.id = vos.order_id AND v.id = vos.vendor_id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """, (st.session_state.user['id'],))
        
        orders = db_executor.fetchall()
        
        if not orders:
            st.info("You have no orders yet.")
            return
        
        # Group orders by order_id
        current_order = None
        items = []
        
        for order in orders:
            if current_order != order[0]:  # order_id
                if current_order is not None:  # If not first order, display previous order's items and buttons
                    # Display all items with their vendor-specific status
                    for item in items:
                        status_text = f" ({item[9] or 'pending'})" if item[9] else ""
                        st.write(f"- {item[6]} x {item[7]} (₹{item[8]:.2f}) from {item[5]}{status_text}")
                    
                    # Add View Invoice button if Razorpay order exists
                    if items[0][4]:  # razorpay_order_id
                        # First check in session state
                        if 'invoices' in st.session_state and str(current_order) in st.session_state.invoices:
                            invoice_url = st.session_state.invoices[str(current_order)]
                            st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
                        else:
                            # If not in session state, try to fetch from Razorpay
                            try:
                                from payment import client
                                invoices = client.invoice.all()
                                for invoice in invoices['items']:
                                    if invoice['notes'].get('order_id') == str(current_order):
                                        invoice_url = invoice['short_url']
                                        st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
                                        # Store in session state for future
                                        if 'invoices' not in st.session_state:
                                            st.session_state.invoices = {}
                                        st.session_state.invoices[str(current_order)] = invoice_url
                                        break
                                else:
                                    st.write("Invoice not found")
                            except Exception as e:
                                st.error(f"Error fetching invoice: {str(e)}")
                    
                    st.write("---")  # Add separator between orders
                    items = []  # Clear items for next order
                
                current_order = order[0]
                st.subheader(f"Order #{order[0]}")
                st.write(f"Status: {order[1]}")
                st.write(f"Total: ₹{order[2]:.2f}")
                st.write(f"Date: {order[3].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write("Items:")
            
            # Add item to current order's items
            items.append(order)
        
        # Display last order's items and buttons
        if items:
            for item in items:
                status_text = f" ({item[9] or 'pending'})" if item[9] else ""
                st.write(f"- {item[6]} x {item[7]} (₹{item[8]:.2f}) from {item[5]}{status_text}")
            
            # Add View Invoice button if Razorpay order exists
            if items[0][4]:  # razorpay_order_id
                # First check in session state
                if 'invoices' in st.session_state and str(current_order) in st.session_state.invoices:
                    invoice_url = st.session_state.invoices[str(current_order)]
                    st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
                else:
                    # If not in session state, try to fetch from Razorpay
                    try:
                        from payment import client
                        invoices = client.invoice.all()
                        for invoice in invoices['items']:
                            if invoice['notes'].get('order_id') == str(current_order):
                                invoice_url = invoice['short_url']
                                st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
                                # Store in session state for future
                                if 'invoices' not in st.session_state:
                                    st.session_state.invoices = {}
                                st.session_state.invoices[str(current_order)] = invoice_url
                                break
                        else:
                            st.write("Invoice not found")
                    except Exception as e:
                        st.error(f"Error fetching invoice: {str(e)}")
        
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        if 'db_executor' in locals():
            db_executor.close()
        if 'conn' in locals():
            conn.close()

def place_order():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        db_executor = conn.cursor()
        
        # Start transaction
        conn.start_transaction()
        
        # Get menu items
        menu_items = get_menu_items()
        if not menu_items:
            print("No items available in the menu.")
            return
        
        # Display menu by vendors
        current_vendor = None
        print("\nAvailable Menu Items:")
        print("=" * 80)
        
        for item in menu_items:
            if current_vendor != item[1]:  # vendor_name
                current_vendor = item[1]
                print(f"\n{current_vendor}:")
                print("-" * 40)
            
            print(f"{item[2]}. {item[3]} - ₹{item[5]:.2f}")
            if item[4]:  # description
                print(f"   {item[4]}")
        
        # Get order items
        order_items = []
        total = 0.0
        
        while True:
            item_id = input("\nEnter item ID to add to cart (or 'done' to finish): ")
            if item_id.lower() == 'done':
                break
                
            try:
                item_id = int(item_id)
                quantity = int(input("Enter quantity: "))
                
                # Find the selected item
                selected_item = next((item for item in menu_items if item[2] == item_id), None)
                if selected_item:
                    order_items.append({
                        'item_id': item_id,
                        'quantity': quantity,
                        'price': selected_item[5]
                    })
                    total += selected_item[5] * quantity
                else:
                    print("Invalid item ID. Please try again.")
            except ValueError:
                print("Please enter valid numbers.")
        
        if not order_items:
            print("No items selected. Order cancelled.")
            return
        
        # Create order
        db_executor.execute(
            "INSERT INTO orders (user_id, total, status) VALUES (%s, %s, 'inmaking')",
            (st.session_state.user['id'], total)
        )
        
        # Get the auto-incremented order ID
        order_id = db_executor.lastrowid
        print(f"\nCreated order with ID: {order_id}")
        
        # Add order items
        for item in order_items:
            db_executor.execute(
                "INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_time) VALUES (%s, %s, %s, %s)",
                (order_id, item['item_id'], item['quantity'], item['price'])
            )
            print(f"Added item {item['item_id']} (quantity: {item['quantity']}) to order {order_id}")
        
        # Commit transaction
        conn.commit()
        print(f"\nOrder placed successfully! Order ID: {order_id}")
        print(f"Total amount: ₹{total:.2f}")
        
        # Verify the order was created
        db_executor.execute("""
            SELECT o.*, v.name as vendor_name, m.name as item_name, 
                   m.price, oi.quantity, oi.price_at_time
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items m ON oi.menu_item_id = m.id
            JOIN vendors v ON m.vendor_id = v.id
            WHERE o.id = %s
        """, (order_id,))
        
        items = db_executor.fetchall()
        if items:
            print("\nOrder verification:")
            print(f"Order ID: {items[0][0]}")
            print(f"User ID: {items[0][1]}")
            print(f"Total: ₹{items[0][2]:.2f}")
            print(f"Status: {items[0][3]}")
            print(f"Created at: {items[0][4]}")
            
            print("\nOrder items:")
            for item in items:
                print(f"Vendor: {item[5]}")
                print(f"Item: {item[6]} x {item[7]}")
                print(f"Price at time: ₹{item[8]:.2f}")
                print("-" * 40)
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        if 'db_executor' in locals():
            db_executor.close()
        if 'conn' in locals():
            conn.close()

def register():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        db_executor = conn.cursor()
        
        print("\n=== Registration ===")
        name = input("Enter your name: ")
        email = input("Enter your email: ")
        password = input("Enter your password: ")
        role = input("Enter your role (user/vendor): ").lower()
        
        # Validate role
        if role not in ['user', 'vendor']:
            print("Invalid role. Please enter 'user' or 'vendor'.")
            return
        
        # Check if email already exists
        db_executor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if db_executor.fetchone():
            print("Email already registered. Please use a different email or login.")
            return
        
        # Insert new user
        db_executor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password, role)
        )
        
        # Commit the transaction
        conn.commit()
        
        print("\nAccount created successfully!")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Role: {role}")
        print("\nYou can now login with your credentials.")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        if 'db_executor' in locals():
            db_executor.close()
        if 'conn' in locals():
            conn.close()

def admin_ui():
    st.title("Admin Dashboard")
    
    # Add tabs for different admin functions
    admin_tab = st.sidebar.radio(
        "Admin Functions",
        ["Vendor Management", "Order Analysis"],
        key="admin_navigation_tabs"
    )
    
    if admin_tab == "Vendor Management":
        st.header("Vendor Management")
        
        # Add new vendor form
        with st.form("add_vendor_form"):
            st.subheader("Add New Vendor")
            vendor_name = st.text_input("Vendor Name")
            vendor_email = st.text_input("Vendor Email")
            vendor_password = st.text_input("Vendor Password", type="password")
            
            if st.form_submit_button("Add Vendor"):
                try:
                    conn = mysql.connector.connect(**DB_CONFIG)
                    db_executor = conn.cursor()
                    
                    # Check if vendor email already exists
                    db_executor.execute("SELECT id FROM users WHERE email = %s", (vendor_email,))
                    if db_executor.fetchone():
                        st.error("Vendor with this email already exists.")
                    else:
                        # Create vendor user
                        db_executor.execute(
                            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'vendor')",
                            (vendor_name, vendor_email, vendor_password)
                        )
                        user_id = db_executor.lastrowid
                        
                        # Create vendor entry
                        db_executor.execute(
                            "INSERT INTO vendors (name, user_id) VALUES (%s, %s)",
                            (vendor_name, user_id)
                        )
                        
                        conn.commit()
                        st.success(f"Successfully added vendor: {vendor_name}")
                        st.rerun()
                        
                except mysql.connector.Error as e:
                    st.error(f"Database error: {e}")
                finally:
                    if 'db_executor' in locals():
                        db_executor.close()
                    if 'conn' in locals():
                        conn.close()
        
        # Remove vendor section
        st.subheader("Remove Vendor")
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            db_executor = conn.cursor()
            
            # Get all vendors
            db_executor.execute("""
                SELECT v.id, v.name, u.email 
                FROM vendors v
                JOIN users u ON v.name = u.name 
                WHERE u.role = 'vendor'
            """)
            vendors = db_executor.fetchall()
            
            if vendors:
                vendor_options = [f"{v[1]} ({v[2]})" for v in vendors]
                selected_vendor = st.selectbox("Select Vendor to Remove", vendor_options)
                
                if st.button("Remove Vendor"):
                    # Get vendor ID from selection
                    vendor_id = vendors[vendor_options.index(selected_vendor)][0]
                    
                    # Delete vendor and associated user
                    db_executor.execute("DELETE FROM vendors WHERE id = %s", (vendor_id,))
                    db_executor.execute("DELETE FROM users WHERE name = (SELECT name FROM vendors WHERE id = %s)", (vendor_id,))
                    
                    conn.commit()
                    st.success(f"Successfully removed vendor: {selected_vendor}")
                    st.rerun()
            else:
                st.info("No vendors found.")
                
        except mysql.connector.Error as e:
            st.error(f"Database error: {e}")
        finally:
            if 'db_executor' in locals():
                db_executor.close()
            if 'conn' in locals():
                conn.close()
    
    elif admin_tab == "Order Analysis":
        st.header("Order Analysis by Vendor")
        
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            db_executor = conn.cursor()
            
            # Get date range for analysis
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            
            # Get vendor-wise order statistics
            db_executor.execute("""
                SELECT 
                    v.name as vendor_name,
                    COUNT(DISTINCT o.id) as total_orders,
                    SUM(oi.quantity) as total_items,
                    SUM(oi.quantity * oi.price_at_time) as total_revenue,
                    AVG(oi.quantity * oi.price_at_time) as avg_order_value
                FROM vendors v
                JOIN menu_items m ON v.id = m.vendor_id
                JOIN order_items oi ON m.id = oi.menu_item_id
                JOIN orders o ON oi.order_id = o.id
                WHERE o.created_at BETWEEN %s AND %s
                GROUP BY v.id, v.name
                ORDER BY total_revenue DESC
            """, (start_date, end_date))
            
            vendor_stats = db_executor.fetchall()
            
            if vendor_stats:
                # Display summary statistics
                st.subheader("Vendor Performance Summary")
                
                # Create columns for metrics
                cols = st.columns(len(vendor_stats))
                for i, (vendor, orders, items, revenue, avg_value) in enumerate(vendor_stats):
                    with cols[i]:
                        st.metric(
                            label=vendor,
                            value=f"₹{revenue:,.2f}",
                            delta=f"{orders} orders"
                        )
                
                # Display detailed statistics in a table
                st.subheader("Detailed Statistics")
                stats_data = {
                    "Vendor": [v[0] for v in vendor_stats],
                    "Total Orders": [v[1] for v in vendor_stats],
                    "Total Items Sold": [v[2] for v in vendor_stats],
                    "Total Revenue": [f"₹{v[3]:,.2f}" for v in vendor_stats],
                    "Average Order Value": [f"₹{v[4]:,.2f}" for v in vendor_stats]
                }
                st.dataframe(stats_data)
                
                # Display revenue trend chart
                st.subheader("Revenue Trend")
                db_executor.execute("""
                    SELECT 
                        DATE(o.created_at) as order_date,
                        v.name as vendor_name,
                        SUM(oi.quantity * oi.price_at_time) as daily_revenue
                    FROM orders o
                    JOIN order_items oi ON o.id = oi.order_id
                    JOIN menu_items m ON oi.menu_item_id = m.id
                    JOIN vendors v ON m.vendor_id = v.id
                    WHERE o.created_at BETWEEN %s AND %s
                    GROUP BY DATE(o.created_at), v.name
                    ORDER BY order_date, v.name
                """, (start_date, end_date))
                
                trend_data = db_executor.fetchall()
                if trend_data:
                    import pandas as pd
                    
                    # Convert to DataFrame and ensure proper data types
                    df = pd.DataFrame(trend_data, columns=['date', 'vendor', 'revenue'])
                    df['revenue'] = df['revenue'].astype(float)  # Ensure revenue is float
                    df['date'] = pd.to_datetime(df['date'])  # Convert date to datetime
                    
                    # Create pivot table for the chart with proper column names
                    pivot_df = df.pivot(index='date', columns='vendor', values='revenue')
                    pivot_df.index.name = 'Date'
                    pivot_df.columns.name = 'Vendor'
                    
                    # Fill NaN values with 0
                    pivot_df = pivot_df.fillna(0)
                    
                    # Add a title above the chart
                    st.markdown("### Daily Revenue Trend by Vendor")
                    
                    # Create a container for the chart
                    chart_container = st.container()
                    
                    # Create columns for layout
                    col1, col2 = st.columns([1, 15])
                    
                    with col1:
                        # Y-axis label
                        st.markdown("""
                        <div style='writing-mode: vertical-lr; 
                        transform: rotate(180deg);
                        text-align: center; 
                        height: 500px; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center;
                        font-weight: bold;
                        font-size: 14px;'>
                        Revenue (₹)
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # X-axis label
                        st.markdown("""
                        <div style='text-align: center; 
                        margin-bottom: 10px;
                        font-weight: bold;
                        font-size: 14px;'>
                        Date
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Chart with custom styling
                        st.line_chart(
                            pivot_df,
                            use_container_width=True,
                            height=500
                        )
                    
                    # Add summary statistics below the chart
                    st.markdown("### Summary Statistics")
                    summary_stats = df.groupby('vendor')['revenue'].agg(['sum', 'mean', 'count']).round(2)
                    summary_stats.columns = ['Total Revenue', 'Average Daily Revenue', 'Number of Days']
                    summary_stats['Total Revenue'] = summary_stats['Total Revenue'].apply(lambda x: f"₹{x:,.2f}")
                    summary_stats['Average Daily Revenue'] = summary_stats['Average Daily Revenue'].apply(lambda x: f"₹{x:,.2f}")
                    
                    # Style the summary table
                    st.dataframe(
                        summary_stats,
                        use_container_width=True,
                        column_config={
                            "Total Revenue": st.column_config.TextColumn(
                                "Total Revenue",
                                help="Total revenue for the selected period"
                            ),
                            "Average Daily Revenue": st.column_config.TextColumn(
                                "Average Daily Revenue",
                                help="Average daily revenue"
                            ),
                            "Number of Days": st.column_config.NumberColumn(
                                "Number of Days",
                                help="Number of days with sales"
                            )
                        }
                    )
            else:
                st.info("No order data found for the selected date range.")
                
        except mysql.connector.Error as e:
            st.error(f"Database error: {e}")
        finally:
            if 'db_executor' in locals():
                db_executor.close()
            if 'conn' in locals():
                conn.close()
