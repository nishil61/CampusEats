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

# ---------- Customer UI ----------
def customer_ui():
    st.header("🍔 Menu")

    # Poll every 5 s to pick up status changes
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
                    "INSERT INTO order_items (order_id, menu_item_id, quantity) VALUES (%s, %s, %s)",
                    (order_id, item_id, qty)
                )
            st.success(f"✅ Order placed! Your order number is #{order_id}")
            st.session_state["cart"] = {}

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
    st.header("🧾 Vendor Dashboard")

    # Poll every 5 s for new status changes
    st_autorefresh(interval=5_000, limit=None, key="vend_poll")

    # 1) orders that are just placed (inmaking)
    st.subheader("👩‍🍳 In‐Making Orders")
    inmaking = execute_query(
        "SELECT o.id, u.email, o.created_at FROM orders o "
        "JOIN users u ON o.user_id=u.id WHERE o.status='inmaking'",
        fetch=True
    )
    for o in inmaking:
        st.write(f"#{o['id']} from {o['email']} at {o['created_at']}")
        if st.button(f"Mark #{o['id']} Ready"):
            execute_query("UPDATE orders SET status='ready' WHERE id=%s", (o["id"],))
            st.success(f"Order #{o['id']} is now Ready.")

    # 2) orders that are ready but not yet picked up
    st.subheader("🔔 Ready for Pick‑Up")
    ready = execute_query(
        "SELECT o.id, u.email, o.created_at FROM orders o "
        "JOIN users u ON o.user_id=u.id WHERE o.status='ready'",
        fetch=True
    )
    for o in ready:
        st.write(f"#{o['id']} for {o['email']} (ready since {o['created_at']})")
        if st.button(f"Mark #{o['id']} Picked Up"):
            execute_query("UPDATE orders SET status='pickedup' WHERE id=%s", (o["id"],))
            st.success(f"Order #{o['id']} marked as Picked Up.")



# ---------- Admin UI (unchanged) ----------
def admin_ui():
    st.title("Admin Dashboard")
    
    # Create tabs for different admin functions
    tab1, tab2 = st.tabs(["Orders", "Menu Management"])
    
    with tab1:
        st.header("Orders")
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="canteen1"
            )
            cursor = conn.cursor()
            
            # Get all orders with improved query to get unique vendors per order
            cursor.execute("""
                SELECT 
                    o.id,
                    o.user_id,
                    o.total,
                    o.status,
                    o.razorpay_order_id,
                    o.created_at,
                    u.email,
                    GROUP_CONCAT(DISTINCT v.name) as vendors,
                    m.name as item_name,
                    oi.quantity,
                    oi.price_at_time,
                    v.name as vendor_name
                FROM orders o
                JOIN users u ON o.user_id = u.id
                JOIN order_items oi ON o.id = oi.order_id
                JOIN menu_items m ON oi.menu_item_id = m.id
                JOIN vendors v ON m.vendor_id = v.id
                GROUP BY o.id, m.id
                ORDER BY o.created_at DESC
            """)
            
            orders = cursor.fetchall()
            
            if not orders:
                st.info("No orders found.")
                return
            
            # Group orders by order_id
            current_order = None
            items = []  # Store items for current order
            
            for order in orders:
                if current_order != order[0]:  # New order
                    if current_order is not None:  # If not first order, display previous order's items and buttons
                        # Display all items
                        for item in items:
                            st.write(f"₹{item[10]:.2f} x {item[9]} (₹{item[10] * item[9]:.2f}) {item[8]} from {item[11]}")
                        
                        # Add status update buttons after all items
                        st.write("---")  # Add separator before buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"Mark Ready #{current_order}"):
                                cursor.execute(
                                    "UPDATE orders SET status = 'ready' WHERE id = %s",
                                    (current_order,)
                                )
                                conn.commit()
                                st.rerun()
                        with col2:
                            if st.button(f"Mark Picked Up #{current_order}"):
                                cursor.execute(
                                    "UPDATE orders SET status = 'pickedup' WHERE id = %s",
                                    (current_order,)
                                )
                                conn.commit()
                                st.rerun()
                        with col3:
                            if items[0][4]:  # Only show invoice button if Razorpay order exists
                                try:
                                    from payment import client
                                    invoices = client.invoice.all()
                                    for invoice in invoices['items']:
                                        if invoice['notes'].get('order_id') == str(current_order):
                                            invoice_url = invoice['short_url']
                                            st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
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
                    # Get user name from users table
                    cursor.execute("SELECT name FROM users WHERE id = %s", (order[1],))
                    user_name = cursor.fetchone()
                    if user_name and user_name[0]:
                        st.write(f"Customer Name: {user_name[0]}")
                    if order[4]:  # razorpay_order_id
                        st.write(f"Razorpay Order ID: {order[4]}")
                    st.write(f"Status: {order[3]}")
                    st.write(f"Total: ₹{order[2]:.2f}")
                    # Format date properly
                    order_date = order[5].strftime("%Y-%m-%d %H:%M:%S")
                    st.write(f"Date: {order_date}")
                    # Display vendors
                    st.write(f"Vendor(s): {order[7]}")
                    st.write("Items:")
                
                # Add item to current order's items
                items.append(order)
            
            # Display last order's items and buttons
            if items:
                for item in items:
                    st.write(f"₹{item[10]:.2f} x {item[9]} (₹{item[10] * item[9]:.2f}) {item[8]} from {item[11]}")
                
                st.write("---")  # Add separator before buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Mark Ready #{current_order}"):
                        cursor.execute(
                            "UPDATE orders SET status = 'ready' WHERE id = %s",
                            (current_order,)
                        )
                        conn.commit()
                        st.rerun()
                with col2:
                    if st.button(f"Mark Picked Up #{current_order}"):
                        cursor.execute(
                            "UPDATE orders SET status = 'pickedup' WHERE id = %s",
                            (current_order,)
                        )
                        conn.commit()
                        st.rerun()
                with col3:
                    if items[0][4]:  # Only show invoice button if Razorpay order exists
                        try:
                            from payment import client
                            invoices = client.invoice.all()
                            for invoice in invoices['items']:
                                if invoice['notes'].get('order_id') == str(current_order):
                                    invoice_url = invoice['short_url']
                                    st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">View Invoice</button></a>', unsafe_allow_html=True)
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
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    with tab2:
        st.header("Menu Management")
        
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="canteen1"
            )
            cursor = conn.cursor()
            
            # Get all vendors
            cursor.execute("SELECT id, name FROM vendors ORDER BY name")
            vendors = cursor.fetchall()
            
            if vendors:
                # Create tabs for each vendor
                vendor_tabs = st.tabs([vendor[1] for vendor in vendors])
                
                for i, (vendor_id, vendor_name) in enumerate(vendors):
                    with vendor_tabs[i]:
                        st.subheader(f"{vendor_name} Menu Items")
                        
                        # Get menu items for this vendor
                        cursor.execute("""
                            SELECT id, name, description, price, available, image_path 
                            FROM menu_items 
                            WHERE vendor_id = %s
                            ORDER BY name
                        """, (vendor_id,))
                        
                        menu_items = cursor.fetchall()
                        
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
                                if st.form_submit_button("Save Changes"):
                                    try:
                                        for item_id, new_status in changes.items():
                                            cursor.execute("""
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
                            st.info(f"No menu items found for {vendor_name}")
                
                # Add new menu item section (for Poornima Kitchen)
                if any(vendor[1] == "Poornima Kitchen" for vendor in vendors):
                    st.markdown("---")
                    st.subheader("Add New Thali Item (Poornima Kitchen)")
                    
                    # Get Poornima Kitchen's vendor_id
                    poornima_vendor_id = next(vendor[0] for vendor in vendors if vendor[1] == "Poornima Kitchen")
                    
                    # Create form for new menu item
                    with st.form("add_menu_item"):
                        # Menu item details
                        name = st.text_input("Item Name (e.g., Monday Special Thali)")
                        description = st.text_area("Description (List the items in thali)")
                        price = st.number_input("Price (₹)", min_value=0.0, step=1.0)
                        available = st.checkbox("Available", value=True)
                        image_path = st.text_input("Image Path (Optional)")
                        
                        # Submit button
                        if st.form_submit_button("Add Menu Item"):
                            if name and description and price > 0:
                                try:
                                    cursor.execute("""
                                        INSERT INTO menu_items 
                                        (vendor_id, name, description, price, available, image_path)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """, (poornima_vendor_id, name, description, price, available, image_path or None))
                                    
                                    conn.commit()
                                    st.success(f"Successfully added {name} to the menu!")
                                    st.rerun()
                                except mysql.connector.Error as e:
                                    st.error(f"Error adding menu item: {e}")
                            else:
                                st.error("Please fill in all required fields (Name, Description, and Price)")
            else:
                st.error("No vendors found in the database")
            
        except mysql.connector.Error as e:
            st.error(f"Database error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
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
        # Connect to database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        cursor = conn.cursor()
        
        for item_id, quantity in st.session_state.cart.items():
            # Get item details from database
            cursor.execute("""
                SELECT m.name, m.price, v.name as vendor_name
                FROM menu_items m
                JOIN vendors v ON m.vendor_id = v.id
                WHERE m.id = %s
            """, (item_id,))
            
            item = cursor.fetchone()
            if item:
                name, price, vendor = item
                item_total = price * quantity
                total += item_total
                st.write(f"{name} (from {vendor}) x {quantity} = ₹{item_total:.2f}")
        
        st.write("---")
        st.write(f"**Total Amount: ₹{total:.2f}**")
        
        if st.button("Place Order"):
            # Create order
            cursor.execute(
                "INSERT INTO orders (user_id, total, status) VALUES (%s, %s, 'inmaking')",
                (st.session_state.user['id'], total)
            )
            
            order_id = cursor.lastrowid
            
            # Add order items
            for item_id, quantity in st.session_state.cart.items():
                cursor.execute("""
                    SELECT price FROM menu_items WHERE id = %s
                """, (item_id,))
                price = cursor.fetchone()[0]
                
                cursor.execute(
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
                cursor.execute(
                    "UPDATE orders SET razorpay_order_id = %s WHERE id = %s",
                    (razorpay_order_id, order_id)
                )
                conn.commit()
                
                # Clear cart
                st.session_state.cart = {}
                
                # Show Razorpay payment
                razorpay_button(
                    amount=total,
                    order_id=order_id,
                    razorpay_order_id=razorpay_order_id,
                    user_name=st.session_state.user['name'],
                    user_email=st.session_state.user['email']
                )
                
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
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def view_my_orders_ui():
    st.title("My Orders")
    
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        cursor = conn.cursor()
        
        # Get user's orders
        cursor.execute("""
            SELECT o.id, o.status, o.total, o.created_at,
                   v.name as vendor_name, m.name as item_name, 
                   oi.quantity, oi.price_at_time
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items m ON oi.menu_item_id = m.id
            JOIN vendors v ON m.vendor_id = v.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """, (st.session_state.user['id'],))
        
        orders = cursor.fetchall()
        
        if not orders:
            st.info("You have no orders yet.")
            return
        
        # Group orders by order_id
        current_order = None
        for order in orders:
            if current_order != order[0]:  # order_id
                current_order = order[0]
                st.subheader(f"Order #{order[0]}")
                st.write(f"Status: {order[1]}")
                st.write(f"Total: ₹{order[2]:.2f}")
                st.write(f"Date: {order[3].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write("Items:")
            
            st.write(f"- {order[5]} x {order[6]} (₹{order[7]:.2f}) from {order[4]}")
        
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
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
        cursor = conn.cursor()
        
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
        cursor.execute(
            "INSERT INTO orders (user_id, total, status) VALUES (%s, %s, 'inmaking')",
            (st.session_state.user['id'], total)
        )
        
        # Get the auto-incremented order ID
        order_id = cursor.lastrowid
        print(f"\nCreated order with ID: {order_id}")
        
        # Add order items
        for item in order_items:
            cursor.execute(
                "INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_time) VALUES (%s, %s, %s, %s)",
                (order_id, item['item_id'], item['quantity'], item['price'])
            )
            print(f"Added item {item['item_id']} (quantity: {item['quantity']}) to order {order_id}")
        
        # Commit transaction
        conn.commit()
        print(f"\nOrder placed successfully! Order ID: {order_id}")
        print(f"Total amount: ₹{total:.2f}")
        
        # Verify the order was created
        cursor.execute("""
            SELECT o.*, v.name as vendor_name, m.name as item_name, 
                   m.price, oi.quantity, oi.price_at_time
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items m ON oi.menu_item_id = m.id
            JOIN vendors v ON m.vendor_id = v.id
            WHERE o.id = %s
        """, (order_id,))
        
        items = cursor.fetchall()
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
        if 'cursor' in locals():
            cursor.close()
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
        cursor = conn.cursor()
        
        print("\n=== Registration ===")
        name = input("Enter your name: ")
        email = input("Enter your email: ")
        password = input("Enter your password: ")
        role = input("Enter your role (admin/vendor/customer): ").lower()
        
        # Validate role
        if role not in ['admin', 'vendor', 'customer']:
            print("Invalid role. Please enter 'admin', 'vendor', or 'customer'.")
            return
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            print("Email already registered. Please use a different email or login.")
            return
        
        # Insert new user
        cursor.execute(
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
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
