import mysql.connector
import os
from dotenv import load_dotenv
import streamlit as st
from config import DB_CONFIG

# Load environment variables
load_dotenv()

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def execute_query(query, params=None, fetch=False):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid
            
        conn.commit()
        return result
        
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        st.error(f"Database error: {str(e)}")
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
