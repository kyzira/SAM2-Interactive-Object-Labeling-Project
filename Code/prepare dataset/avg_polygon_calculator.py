"""
This code scans the masks and labels folder, creates polygon coordinates, calculates the average shape, and saves those coordinates to a txt file with its corresponding damage code.
"""

import os
import csv
import numpy as np
from skimage import measure
from PIL import Image
from scipy.spatial import procrustes

main_path = r"C:\Code Python\automation-with-sam2\labeling_project"  # Set the main path to your directory

def get_damage_code_from_csv(label_dir, folder_name):
    csv_path = os.path.join(label_dir, folder_name + '_labels.csv')
    
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            try:
                next(reader)  # Skip the first row
                second_row = next(reader)  # Get the second row
                
                if second_row and len(second_row) > 0:
                    damage_code = second_row[0]  # First column of the second row
                    return damage_code
            except StopIteration:
                # Handle case where there isn't a second row
                print(f"No second row found in {csv_path}")
                return None
    
    print(f"File {csv_path} does not exist")
    return None

def process_masks_and_save_polygons(frame_dir, mask_dir, damage_code):
    output_dir = r"C:\Code Python\automation-with-sam2\labeling_project\avg polygons"
    os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists
    output_file = os.path.join(output_dir, f'{damage_code}_polygons.txt')
    
    polygons = []  # To store all polygons for this damage code
    
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

                    # Save the polygon coordinates to the file and store them
                    if len(segmentation) >= 6:  # Ensure a valid polygon
                        coords_str = ','.join([f'{x},{y}' for x, y in zip(segmentation[::2], segmentation[1::2])])
                        f.write(f'{coords_str}\n')
                        polygon = [(x, y) for x, y in zip(segmentation[::2], segmentation[1::2])]
                        polygons.append(np.array(polygon))
    
    if polygons:
        mean_shape = compute_mean_shape(polygons)
        save_mean_shape(mean_shape, damage_code, output_dir)

def compute_mean_shape(polygons):
    """
    Compute the mean shape of a set of polygons using Procrustes analysis.
    
    Args:
        polygons (list of np.array): List of polygons (each polygon is a list of (x, y) points).
        
    Returns:
        np.array: The mean shape polygon.
    """
    # Normalize all polygons to have the same number of points
    num_points = min(len(polygon) for polygon in polygons)
    polygons_resampled = [polygon[:num_points] for polygon in polygons]
    
    # Perform Procrustes analysis to align the shapes
    mean_shape = polygons_resampled[0]
    for polygon in polygons_resampled[1:]:
        _, aligned_polygon, _ = procrustes(mean_shape, polygon)
        mean_shape = (mean_shape + aligned_polygon) / 2  # Running average
    
    return mean_shape

def save_mean_shape(mean_shape, damage_code, output_dir):
    """
    Save the mean shape to a text file.
    
    Args:
        mean_shape (np.array): The computed mean shape.
        damage_code (str): The damage code used as the filename.
        output_dir (str): Directory to save the result.
    """
    output_file = os.path.join(output_dir, f'{damage_code}_mean_shape.txt')
    with open(output_file, 'w') as f:
        for point in mean_shape:
            f.write(f'{point[0]},{point[1]}\n')

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
