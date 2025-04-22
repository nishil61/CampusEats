# Food Ordering System

A web-based food ordering system built with Python and Streamlit, featuring multiple vendors, real-time order tracking, and secure payment integration.

## Features

- Multi-vendor support (Fee Fa Foo, Mech Cafe, Poornima Kitchen, Nescafe)
- Real-time order tracking
- Secure payment integration with Razorpay
- Admin dashboard for order management
- Vendor-specific menu management
- Automated invoice generation
- Image support for menu items

## Tech Stack

- Python
- Streamlit
- MySQL
- Razorpay API
- PIL (Python Imaging Library)

## Setup Instructions

1. Clone the repository
```bash
git clone <repository-url>
cd food-order-website
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
Create a `.env` file with:
```
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
```

4. Set up the database
```bash
python setup_database.py
```

5. Run the application
```bash
streamlit run main.py
```

## Project Structure

- `main.py` - Main application entry point
- `ui.py` - User interface components
- `menu_display.py` - Menu display functionality
- `payment.py` - Payment integration
- `auth.py` - Authentication system
- `db.py` - Database operations
- `components/` - Reusable UI components
- `images/` - Menu item images

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 