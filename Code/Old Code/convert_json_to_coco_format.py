import os
import json
import yaml
from PIL import Image 

def rename_frame_and_copy_to_new_location(source_image_path, output_folder, new_filename):
    # Check if the source image exists
    if not os.path.exists(source_image_path):
        print(f"Image not found: {source_image_path}")
        return None, None

    destination_path = os.path.join(output_folder, new_filename)
    img = Image.open(source_image_path)
    img.save(destination_path)  # Use save instead of copy for compatibility

    return img.width, img.height

def add_entry_to_coco(filename, width, height, frame_observations):
    img_id = int(filename.split(".")[0])  # Assuming filename format '00000001.jpg'
    cat_id = 0

    image_info = {
        "id": img_id,
        "width": width,
        "height": height,
        "file_name": filename
    }
    coco_data["images"].append(image_info)

    for key, value in frame_observations.items():
        observation = key.split(" ")[0]
        
        if observation not in category_list:
            category_list.append(observation)
            cat_id = category_list.index(observation) + 1
            category_info = {
                "id": cat_id,
                "name": observation
            }
            coco_data["categories"].append(category_info)
        else:
            cat_id = category_list.index(observation) + 1

        # Process each polygon in the mask polygons directly
        if "Mask Polygon" in value:
            for polygon in value["Mask Polygon"]:

                if len(polygon) < 4:
                    continue
                
                annotation_info = {
                    "id": len(coco_data["annotations"]) + 1,  # Unique annotation ID
                    "image_id": img_id,
                    "category_id": cat_id,
                    "segmentation": polygon,
                    "area": calculate_area(polygon),
                    "iscrowd": 0
                }
                coco_data["annotations"].append(annotation_info)

def calculate_area(polygon):
    # Using Shoelace formula to calculate the area of the polygon
    area = 0
    n = len(polygon)  # Number of vertices
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]  # Next vertex (wrap around to first)
        area += x1 * y2 - x2 * y1
    return abs(area) / 2

def process_json_and_move_frames(frame_folder, output_folder, frame_counter):
    os.makedirs(output_folder, exist_ok=True)

    for json_file in os.listdir(frame_folder):
        if not json_file.endswith('.json'):
            continue

        json_path = os.path.join(frame_folder, json_file)
        with open(json_path, 'r') as file:
            data = json.load(file)

        for value in data.values():
            if "File Name" not in value:
                continue

            frame_filename = value["File Name"]
            frame_observations = value["Observations"]
            source_image_path = os.path.join(frame_folder, "source images", frame_filename)
            new_filename = f"{frame_counter:08d}.jpg"  # Numeric filename

            width, height = rename_frame_and_copy_to_new_location(source_image_path, output_folder, new_filename)

            if width is not None and height is not None:  # Only add if image exists
                add_entry_to_coco(new_filename, width, height, frame_observations)

            frame_counter += 1
    
    return frame_counter

if __name__ == "__main__":

    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    config_path = os.path.join(script_dir, "..", "config.yaml")  # Adjust the path as needed
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    

    json_folder_dir = os.path.join(config['default_paths'].get('output_path'), "results")
    output_folder_path =  os.path.join(config['default_paths'].get('output_path'), "coco_format")
    frame_counter = 1

    coco_data = {
        "images": [],
        "annotations": [],
        "categories": []
    }
    category_list = []

    for folder in os.listdir(json_folder_dir):
        json_folder_path = os.path.join(json_folder_dir, folder)
        frame_counter = process_json_and_move_frames(json_folder_path, os.path.join(output_folder_path, "images"), frame_counter)

    with open(os.path.join(output_folder_path, 'coco_annotations.json'), 'w') as coco_file:
        json.dump(coco_data, coco_file, indent=4)

    print("Processing completed. COCO annotations saved.")
