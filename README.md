# Food Ordering System

A Streamlit-based food ordering application with Razorpay payment integration.

## Features

- Menu browsing by vendor
- Shopping cart functionality
- Order management
- Razorpay payment integration
- Invoice generation and viewing

## Local Development Setup

1. Clone the repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a .env file with the following content:
   ```
   # Database Configuration
   DB_HOST=localhost
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=canteen1

   # Razorpay Configuration
   RAZORPAY_KEY_ID=your_razorpay_key_id
   RAZORPAY_KEY_SECRET=your_razorpay_key_secret
   ```
4. Run the application:
   ```
   streamlit run app.py
   ```

## Deployment

### Streamlit Cloud Deployment

1. Push your code to a GitHub repository
2. Visit [Streamlit Cloud](https://share.streamlit.io/)
3. Sign in with GitHub
4. Deploy your app by selecting your repository
5. Add the following secrets in the Streamlit Cloud dashboard:
   - DB_HOST
   - DB_USER
   - DB_PASSWORD
   - DB_NAME
   - RAZORPAY_KEY_ID
   - RAZORPAY_KEY_SECRET

### Database Setup for Production

For production deployment, you will need a cloud-hosted MySQL database. Options include:

1. PlanetScale (has a free tier)
2. AWS RDS
3. Google Cloud SQL
4. Azure Database for MySQL

Update your database connection details in the Streamlit Cloud dashboard secrets.

## Important Notes for Deployment

1. The local MySQL database will not be accessible from Streamlit Cloud. You'll need to use a cloud-hosted database.
2. Make sure all dependencies are listed in requirements.txt
3. Set up environment variables in Streamlit Cloud for sensitive information

## Contributors

Nishil, Krutagna, Jenish and Khushi 