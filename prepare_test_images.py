import os
from PIL import Image

def rename_images_in_directory(directory):
    # List all files in the directory
    files = os.listdir(directory)
    
    # Filter out only image files
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
    # Sort the image files
    image_files.sort()
    
    # Rename images
    for index, file_name in enumerate(image_files):
        # Construct the new file name with leading zeros
        new_file_name = f"{index:05d}.jpg"
        
        # Full path to the old file
        old_file_path = os.path.join(directory, file_name)
        
        # Full path to the new file
        new_file_path = os.path.join(directory, new_file_name)
        
        # Open the image file and save it with the new name
        with Image.open(old_file_path) as img:
            img.save(new_file_path, "JPEG")
        
        # Optionally remove the old file
        os.remove(old_file_path)
        
        print(f"Renamed {file_name} to {new_file_name}")

# Example usage:
directory = r"C:\Users\K3000\Videos\aaa_apart"
rename_images_in_directory(directory)
