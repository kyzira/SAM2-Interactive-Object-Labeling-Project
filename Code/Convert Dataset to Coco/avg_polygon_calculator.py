"""
This Code scans the masks and labels folder, creates polygon coordinates and saves those coordinates to a txt file with its according damage code.
"""


import os
import csv
import numpy as np
from skimage import measure
from PIL import Image

main_path = r"C:\Code Python\automation-with-sam2\labeling_project"  # Set the main path to your directory

def get_damage_code_from_csv(label_dir, folder_name):
    csv_path = os.path.join(label_dir, folder_name + '_labels.csv')
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the first row
            second_row = next(reader)  # Get the second row
            damage_code = second_row[0]  # First column of the second row
            return damage_code
    return None

def process_masks_and_save_polygons(frame_dir, mask_dir, damage_code):
    output_file = os.path.join(r"C:\Code Python\automation-with-sam2\labeling_project\avg polygons", f'{damage_code}.txt')
    
    with open(output_file, 'w') as f:
        for mask_filename in os.listdir(mask_dir):
            if mask_filename.endswith('.png'):
                # Get corresponding image name
                image_filename = mask_filename.replace('.png', '.jpg')
                image_path = os.path.join(frame_dir, image_filename)
                
                # Skip if the image doesn't exist
                if not os.path.exists(image_path):
                    continue

                # Load and process mask
                mask_path = os.path.join(mask_dir, mask_filename)
                mask = np.array(Image.open(mask_path).convert('1'))  # Convert to binary
                
                # Find contours (bounding polygons)
                contours = measure.find_contours(mask, 0.5)
                
                for contour in contours:
                    # Flip and flatten contour to a list of coordinates
                    contour = np.flip(contour, axis=1)
                    segmentation = contour.ravel().tolist()

                    # Save the polygon coordinates to the file
                    if len(segmentation) >= 6:  # Ensure a valid polygon
                        coords_str = ','.join([f'{x},{y}' for x, y in zip(segmentation[::2], segmentation[1::2])])
                        f.write(f'{coords_str}\n')

def main():
    label_dir = os.path.join(main_path, "labels")
    image_dir = os.path.join(main_path, "masks")
    for folder_name in os.listdir(image_dir):
        frame_dir = os.path.join(image_dir, folder_name)
        mask_dir = os.path.join(frame_dir, "masks")
        print(frame_dir)
        if os.path.isdir(mask_dir):
            # Get damage code from the corresponding label file
            damage_code = get_damage_code_from_csv(label_dir, folder_name)
            
            if damage_code:
                process_masks_and_save_polygons(frame_dir, mask_dir, damage_code)

if __name__ == "__main__":
    main()
