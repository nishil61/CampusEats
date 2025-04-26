import mysql.connector
import os
from PIL import Image
import io
import requests
import traceback
from config import DB_CONFIG

def convert_image_to_blob(image_path):
    try:
        print(f"\nProcessing image: {image_path}")
        
        # Check if the path is a URL
        if isinstance(image_path, str) and image_path.startswith(('http://', 'https://')):
            print("Downloading image from URL...")
            response = requests.get(image_path)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
            else:
                print(f"Failed to download image from URL: {image_path}")
                return None
        else:
            # Handle local file path
            if isinstance(image_path, bytes):
                image_path = image_path.decode('utf-8')
            
            print(f"Looking for local image at: {image_path}")
            if not os.path.exists(image_path):
                print(f"Image file not found: {image_path}")
                return None
            
            try:
                image = Image.open(image_path)
            except Exception as e:
                print(f"Error opening image file: {str(e)}")
                return None
        
        print(f"Image size before resize: {image.size}")
        try:
            image.thumbnail((400, 400))  # Resize to reasonable dimensions
            print(f"Image size after resize: {image.size}")
        except Exception as e:
            print(f"Error resizing image: {str(e)}")
            return None
        
        try:
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=95)
            img_byte_arr = img_byte_arr.getvalue()
            print(f"Image converted to blob, size: {len(img_byte_arr)} bytes")
            return img_byte_arr
        except Exception as e:
            print(f"Error converting image to blob: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Unexpected error in convert_image_to_blob: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return None

def update_database_with_blobs():
    try:
        print("Connecting to database...")
        # Connect to database
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor()
        
        print("Checking if image_blob column exists...")
        # Check if image_blob column exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'menu_items'
            AND column_name = 'image_blob'
        """)
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            print("Adding image_blob column...")
            # Add image_blob column
            cursor.execute("""
                ALTER TABLE menu_items 
                ADD COLUMN image_blob LONGBLOB
            """)
            print("Added image_blob column to menu_items table")
        else:
            print("image_blob column already exists")
        
        print("Fetching menu items with image paths...")
        # Get all menu items with image paths
        cursor.execute("SELECT id, name, image_path FROM menu_items WHERE image_path IS NOT NULL")
        menu_items = cursor.fetchall()
        print(f"Found {len(menu_items)} menu items with image paths")
        
        for item_id, name, image_path in menu_items:
            print(f"\nProcessing menu item: {name}")
            
            # Convert bytes to string if necessary
            if isinstance(image_path, bytes):
                image_path = image_path.decode('utf-8')
            
            print(f"Image path: {image_path}")
            
            # Convert image to blob
            image_blob = convert_image_to_blob(image_path)
            
            if image_blob:
                print("Updating database with image blob...")
                # Update the database with the blob
                cursor.execute("""
                    UPDATE menu_items 
                    SET image_blob = %s 
                    WHERE id = %s
                """, (image_blob, item_id))
                print(f"Successfully updated image for {name}")
            else:
                print(f"Failed to convert image for {name}")
        
        # Commit changes
        print("Committing changes to database...")
        conn.commit()
        print("\nAll images have been converted to blob format and updated in the database")
        
        # Verify the updates
        cursor.execute("SELECT COUNT(*) FROM menu_items WHERE image_blob IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"Total items with blob images: {count}")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        print("Traceback:")
        print(traceback.format_exc())
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Traceback:")
        print(traceback.format_exc())
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_database_with_blobs() 