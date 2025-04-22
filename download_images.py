import os
import requests
from PIL import Image
from io import BytesIO

# Food images with actual URLs for your menu items
FOOD_IMAGES = {
    # Fee Fa Foo (Chinese items)
    'chinese': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrSodh2_bz3T_LLA16yP9WdpyAoAUkC5-TdA&s',
    'manchurian': 'https://t4.ftcdn.net/jpg/08/02/44/25/240_F_802442564_uHRiD5Lc3GUHoO4DJjjqtjOLj5Qwg5fC.jpg',
    'dabeli': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRotd0oa7C7UnNhWEd6lVmtdPe_IEFWK2k_Sg&s',
    'vadapav': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQDmGkPbMl9EwqNvX6-kmJffgtRv2KMEEd9_A&s',
    'katka dabeli': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQpY_DbKckajAXjQQI3zj6Nwh2ahC2Jw-51MQ&s',
    
    # Mech Cafe (Dabeli and Vadapav)
    'butter puff': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGBZV1ndZ5GIEPM4zn5FIlImivVsdTYpPm6w&s',
    'chinese puff': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQQPJYCaraB1bRBWbR7qoi5adO_uIO5Zmto1w&s',
    'butter garlic puff': 'https://www.mrpuff.in/polkadot/files/item/primary_photo/5f21d4de-a014-4dc1-81e2-3592ac68b92b/big_3.1.jpg',
    
    # Poornima Kitchen (Puffs)
    'chocolate ice cream': 'https://www.foodnetwork.com/content/dam/images/food/fullset/2013/4/4/0/EA0905_Chocolate-Ice-Cream_s4x3.jpg',
    'thums-up': 'https://www.bigbasket.com/media/uploads/p/xl/251014_12-thums-up-soft-drink.jpg',
    'bread pakoda': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTsI1_chQWTlfk6HkfSW4wuVAes3BT6JEztGg&s',
    'bhajiya': 'https://as1.ftcdn.net/jpg/03/92/01/50/1000_F_392015001_We0xdUb6hCzVhGJhSp9CyXgfNaXupmTB.jpg',
    
    # Nescafe (Ice cream, drinks, and snacks)
    'garlic bread': 'https://i.pinimg.com/564x/99/7b/ec/997becc1d15d90e4c042bb42037237b5.jpg',
    'veg. sandwich': 'https://www.mrbrownbakery.com/public/image/images/OPK5fIO4Y22wgtUYdAWNGQUBsu4qFJ1tXqCipLe8.jpeg?p=full',
    'maggie': 'https://content.jdmagicbox.com/comp/pune/g3/020pxx20.xx20.190418190355.v6g3/catalogue/queens-maggie-fries-pimple-saudagar-pune-street-food-afvwgkq3qm.jpg',
    'tea': 'https://services.uresthome.com/wp-content/uploads/2023/04/Masala-Chai-Tea-Recipe-Card.webp',
    'coffee': 'https://www.nestleprofessional.com.my/sites/default/files/styles/np_hero_small_small/public/2022-11/Coffee_Soluble-Coffee.jpg?itok=d4GMr782'
}

def download_image(url, filename):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            # Resize image to a reasonable size
            image.thumbnail((800, 800))
            image.save(os.path.join('images', filename))
            return True
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
    return False

def main():
    # Create images directory if it doesn't exist
    if not os.path.exists('images'):
        os.makedirs('images')
    
    # Download images for all menu items
    for item_name, url in FOOD_IMAGES.items():
        # Convert item name to lowercase and replace spaces with underscores
        filename = f"{item_name.lower().replace(' ', '_')}.jpg"
        if download_image(url, filename):
            print(f"Downloaded {filename} for {item_name}")
        else:
            print(f"Failed to download {filename} for {item_name}")

if __name__ == "__main__":
    main() 