import mysql.connector
import os

def check_and_fix_image_paths():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        cursor = conn.cursor()
        
        # Get all menu items with image paths
        cursor.execute("SELECT id, name, image_path FROM menu_items WHERE image_path IS NOT NULL")
        menu_items = cursor.fetchall()
        
        print(f"Found {len(menu_items)} menu items with image paths")
        
        # Get the current working directory
        current_dir = os.getcwd()
        print(f"Current directory: {current_dir}")
        
        # Create images directory if it doesn't exist
        images_dir = os.path.join(current_dir, 'images')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            print(f"Created images directory at: {images_dir}")
        
        for item_id, name, image_path in menu_items:
            print(f"\nChecking item: {name}")
            
            # Convert bytes to string if necessary
            if isinstance(image_path, bytes):
                image_path = image_path.decode('utf-8')
            
            print(f"Current image path: {image_path}")
            
            # Convert path to use forward slashes
            image_path = image_path.replace('\\', '/')
            
            # Check if path is relative
            if not os.path.isabs(image_path):
                # Make path relative to current directory
                new_path = os.path.join('images', os.path.basename(image_path))
                new_path = new_path.replace('\\', '/')
            else:
                # If absolute path, just use the filename
                new_path = os.path.join('images', os.path.basename(image_path))
                new_path = new_path.replace('\\', '/')
            
            print(f"New image path: {new_path}")
            
            # Update the database with the new path
            cursor.execute("""
                UPDATE menu_items 
                SET image_path = %s 
                WHERE id = %s
            """, (new_path, item_id))
            
            print(f"Updated path for {name}")
        
        # Commit changes
        conn.commit()
        print("\nAll image paths have been updated")
        
        # Verify the updates
        cursor.execute("SELECT COUNT(*) FROM menu_items WHERE image_path LIKE 'images/%'")
        count = cursor.fetchone()[0]
        print(f"Total items with corrected paths: {count}")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Error details: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_and_fix_image_paths() 