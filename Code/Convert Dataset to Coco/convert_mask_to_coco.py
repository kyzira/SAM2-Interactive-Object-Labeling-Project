import os
import json
import numpy as np
from skimage import measure
from PIL import Image
import cv2

# Initialize COCO format dictionary
coco = {
    "info": {
        "description": "Dataset",
        "version": "1.0",
        "year": 2024,
    },
    "licenses": [],
    "images": [],
    "annotations": [],
    "categories": []
}

# Define your categories

categories = [
    {"id": 1, "name": "BCAAA", "supercategory": "none"},
    {"id": 2, "name": "BCAEA", "supercategory": "none"},
    {"id": 3, "name": "BCADA", "supercategory": "none"},
    {"id": 4, "name": "BAHC", "supercategory": "none"},
    {"id": 5, "name": "BBBA", "supercategory": "none"},
    {"id": 6, "name": "BBCC", "supercategory": "none"},
    {"id": 7, "name": "BABBA", "supercategory": "none"},
    {"id": 8, "name": "BAJC", "supercategory": "none"},
    {"id": 9, "name": "BAJB", "supercategory": "none"},
    {"id": 10, "name": "BDDB", "supercategory": "none"},
    {"id": 11, "name": "BABBB", "supercategory": "none"},
    {"id": 12, "name": "BCBZD", "supercategory": "none"},
    {"id": 13, "name": "BAG", "supercategory": "none"},
    {"id": 14, "name": "BCAGA", "supercategory": "none"},
    {"id": 15, "name": "BCBZZ", "supercategory": "none"},
    {"id": 16, "name": "BABAA", "supercategory": "none"},
    {"id": 17, "name": "BAFCE", "supercategory": "none"},
    {"id": 18, "name": "BCAZA", "supercategory": "none"},
    {"id": 19, "name": "BCBZC", "supercategory": "none"},
    {"id": 20, "name": "BABBC", "supercategory": "none"},
    {"id": 21, "name": "BCABA", "supercategory": "none"},
    {"id": 22, "name": "BBAB", "supercategory": "none"},
    {"id": 23, "name": "BCAAB", "supercategory": "none"},
    {"id": 24, "name": "BAFAE", "supercategory": "none"},
    {"id": 25, "name": "BAFBE", "supercategory": "none"},
    {"id": 26, "name": "BACB", "supercategory": "none"},
    {"id": 27, "name": "BBBZ", "supercategory": "none"},
    {"id": 28, "name": "BAO", "supercategory": "none"},
    {"id": 29, "name": "BAFJE", "supercategory": "none"},
    {"id": 30, "name": "BAAA", "supercategory": "none"},
    {"id": 31, "name": "BCCAY", "supercategory": "none"},
    {"id": 32, "name": "BCCBY", "supercategory": "none"},
    {"id": 33, "name": "BDDA", "supercategory": "none"},
    {"id": 34, "name": "BBFA", "supercategory": "none"},
    {"id": 35, "name": "BCBZB", "supercategory": "none"},
    {"id": 36, "name": "BBAC", "supercategory": "none"},
    {"id": 37, "name": "BBCB", "supercategory": "none"},
    {"id": 38, "name": "BAIZ", "supercategory": "none"},
    {"id": 39, "name": "BDDC", "supercategory": "none"},
    {"id": 40, "name": "BAJA", "supercategory": "none"},
    {"id": 41, "name": "BBFC", "supercategory": "none"},
    {"id": 42, "name": "BBCA", "supercategory": "none"},
    {"id": 43, "name": "BAHB", "supercategory": "none"},
    {"id": 44, "name": "BCACA", "supercategory": "none"},
    {"id": 45, "name": "BCCYB", "supercategory": "none"},
    {"id": 46, "name": "BAP", "supercategory": "none"}
]


coco['categories'] = categories

main_path = r""

label_dir = os.path.join(main_path, "labels")
masks_dir = os.path.join(main_path, "masks")


def process_masks(frame_dir, mask_dir):
    for mask_filename in os.listdir(mask_dir):
        print(mask_filename)
        if mask_filename.endswith('.png'):
            # Parse mask filename
            parts = mask_filename.split('-')
            image_filename = f'{parts[0]}-{parts[1]}.jpg'  # Assuming task-4925.jpg format for image filename
            category_name = parts[7]  # Extracts the category name like "Connections"
            
            # Get corresponding image
            image_path = os.path.join(frame_dir, image_filename)
            if not os.path.exists(image_path):
                continue

            image_id = int(parts[1])  # Assuming task-4925 => image_id = 4925
            
            # Read image and get its dimensions
            image = Image.open(image_path)
            width, height = image.size
            
            # Add image info to COCO dictionary (if not already added)
            if not any(img['id'] == image_id for img in coco['images']):
                coco['images'].append({
                    "id": image_id,
                    "file_name": image_filename,
                    "width": width,
                    "height": height
                })
            
            # Process mask
            mask_path = os.path.join(masks_dir, mask_filename)
            mask = np.array(Image.open(mask_path).convert('1'))  # Convert to binary
            
            # Find contours (bounding polygons)
            contours = measure.find_contours(mask, 0.5)
            
            for contour in contours:
                contour = np.flip(contour, axis=1)
                segmentation = contour.ravel().tolist()

                # Ensure the segmentation has more than 4 points to form a valid polygon
                if len(segmentation) >= 6:
                    # Calculate bounding box for completeness (not used in YOLO format)
                    x, y, w, h = cv2.boundingRect(contour.astype(np.int32))

                    # Add annotation info to COCO dictionary
                    coco['annotations'].append({
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": get_category_id(category_name),
                        "segmentation": [segmentation],
                        "bbox": [x, y, w, h],
                        "area": w * h,
                        "iscrowd": 0
                    })
                    annotation_id += 1




def main():
    for mask_file in os.listdir(masks_dir):
        frame_dir = os.path.join(masks_dir, mask_file)
        if os.path.isdir(frame_dir):
            mask_dir = os.path.join(frame_dir, "masks")
            if os.path.isdir(mask_dir):
                process_masks(frame_dir, mask_dir)







# Save to JSON
with open(output_json, 'w') as f:
    json.dump(coco, f, indent=4)

print(f"COCO annotations saved to {output_json}")
