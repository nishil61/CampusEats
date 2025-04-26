# Campus Eats - Food Ordering System

A modern, user-friendly food ordering system designed for campus environments, featuring multi-vendor support, real-time order tracking, and secure payment processing.

## 🚀 Features

- **Multi-Role System**
  - User: Browse menu, place orders, track order status
  - Vendor: Manage menu, process orders, update order status
  - Admin: Manage vendors, analyze order data

- **Order Management**
  - Real-time order tracking
  - Multi-vendor order support
  - Order history and status updates

- **Menu Management**
  - Dynamic menu updates
  - Item availability control
  - Price management

- **Payment Integration**
  - Secure payment processing
  - Order invoice generation
  - Payment status tracking

## 🛠️ Prerequisites

- Python 3.8 or higher
- MySQL Server
- Streamlit
- Razorpay account (for payment processing)

## 📦 Installation

1. **Clone the Repository**
   ```bash
   git clone [repository-url]
   cd food_order_website
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   - Create a MySQL database named `canteen1`
   - Update database credentials in `config.py`:
     ```python
     DB_CONFIG = {
         'host': 'localhost',
         'user': 'your_username',
         'password': 'your_password',
         'database': 'canteen1'
     }
     ```

5. **Initialize Database**
   ```bash
   python create_tables.py
   ```

6. **Configure Payment Gateway**
   - Update Razorpay credentials in `payment.py`:
     ```python
     RAZORPAY_KEY_ID = 'your_key_id'
     RAZORPAY_KEY_SECRET = 'your_key_secret'
     ```

## 🚀 Running the Application

1. **Start the Application**
   ```bash
   streamlit run main.py
   ```

2. **Access the Application**
   - Open your browser and navigate to `http://localhost:8501`

## 👥 User Guide

### For Customers
1. **Registration**
   - Click "Sign Up" and fill in your details
   - Choose "user" as your role
   - Verify your email and set a password

2. **Placing Orders**
   - Browse the menu
   - Add items to cart
   - Proceed to checkout
   - Complete payment
   - Track order status

### For Vendors
1. **Registration**
   - Contact admin for vendor account creation
   - Use provided credentials to login

2. **Menu Management**
   - Add/remove menu items
   - Update prices
   - Manage item availability

3. **Order Processing**
   - View incoming orders
   - Update order status
   - Mark orders as ready/picked up

### For Admins
1. **Vendor Management**
   - Add new vendors
   - Remove vendors
   - Monitor vendor performance

2. **Analytics**
   - View order statistics
   - Analyze vendor performance
   - Generate reports

## 🔒 Security Features

- Password hashing
- Role-based access control
- Secure payment processing
- Session management

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: MySQL
- **Payment Gateway**: Razorpay
- **Authentication**: Custom implementation

## 📝 API Documentation

### Authentication Endpoints
- `/login` - User authentication
- `/signup` - User registration
- `/logout` - Session termination

### Order Endpoints
- `/orders` - Order management
- `/menu` - Menu operations
- `/payment` - Payment processing

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Nishil
- Krutagna
- Jenish
- Khushi

## 🙏 Acknowledgments

- Streamlit team for the amazing framework
- Razorpay for payment integration
- MySQL for database support 