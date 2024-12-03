import os
import json
from PIL import Image, ImageDraw
import shutil

def generate_masks(dataset_path, output_path):
    folder_list = os.listdir(dataset_path)
    for list_index, video_folder in enumerate(folder_list):
        video_folder_cleaned = os.path.splitext(video_folder)[0]
        
        try:
            images_output_path = os.path.join(output_path, "Images")
            masks_output_path = os.path.join(output_path, "Masks")

            video_path = os.path.join(dataset_path, video_folder)
            if not os.path.isdir(video_path):
                continue

            json_file = [f for f in os.listdir(video_path) if f.endswith('.json')]
            if len(json_file) != 1:
                print(f"JSON file not found or multiple JSONs in {video_path}")
                continue
            json_path = os.path.join(video_path, json_file[0])

            with open(json_path, 'r') as f:
                annotations = json.load(f)

            images_path = os.path.join(video_path, "source images")
            if not os.path.exists(images_path):
                print(f"Source images directory not found in {video_path}")
                continue

            images_output_path = os.path.join(images_output_path, video_folder_cleaned)
            masks_output_path = os.path.join(masks_output_path, video_folder_cleaned)
        except Exception as e:
            print(f"Error processing folder {video_folder}: {e}")
            continue

        os.makedirs(images_output_path, exist_ok=True)
        os.makedirs(masks_output_path, exist_ok=True)

        any_mask_saved = False  # Track if any masks were saved in the current folder
        output_index = 0  # Counter for naming output images and masks sequentially

        for image_file in sorted(os.listdir(images_path)):  # Ensure files are processed in order
            if not image_file.endswith('.jpg'):
                continue

            image_number = str(int(os.path.splitext(image_file)[0]))

            if image_number not in annotations:
                print(f"No annotations for {image_file}")
                continue

            image_path = os.path.join(images_path, image_file)
            with Image.open(image_path) as img:
                width, height = img.size

            COLOR_MAP = {
                1: (255, 0, 0),
                2: (0, 255, 0),
                3: (0, 0, 255),
                4: (255, 255, 0),
                5: (255, 0, 255),
                6: (0, 255, 255),
            }

            mask = Image.new("RGB", (width, height), (0, 0, 0))
            draw = ImageDraw.Draw(mask)
            observations = annotations[image_number]["Observations"]

            mask_has_data = False  # Track if this mask has any content
            for category_idx, observation in enumerate(observations.values(), start=1):
                for mask_polygon in observation.get("Mask Polygon", []):
                    points = [(int(point[0]), int(point[1])) for point in mask_polygon]
                    if len(points) > 2:
                        mask_has_data = True
                        color = COLOR_MAP.get(category_idx, (255, 255, 255))
                        draw.polygon(points, fill=color)

            if mask_has_data:
                # Save the image and mask with sequential naming
                image_output_path = os.path.join(images_output_path, f"{output_index:05d}.jpg")
                mask_output_path = os.path.join(masks_output_path, f"{output_index:05d}.png")

                shutil.copy(image_path, image_output_path)
                mask.save(mask_output_path)

                any_mask_saved = True
                output_index += 1  # Increment the counter only when a valid image and mask are saved

                print(f"Folder {list_index}/{len(folder_list)}, Saved image: {image_output_path}, mask: {mask_output_path}")
            else:
                print(f"No mask data for {image_file}, skipped.")

        if not any_mask_saved:
            # Delete the folders if no masks were saved
            shutil.rmtree(masks_output_path, ignore_errors=True)
            shutil.rmtree(images_output_path, ignore_errors=True)
            print(f"Deleted empty folders: {masks_output_path} and {images_output_path}")

def clean_folders(folder_dir):
    mask_dir = os.path.join(folder_dir, "Masks")
    image_dir = os.path.join(folder_dir, "Images")
    folders_to_delete = []

    for folder in os.listdir(mask_dir):
        to_check_folder = os.path.join(mask_dir, folder)
        if len(os.listdir(to_check_folder)) < 6:
            folders_to_delete.append((to_check_folder, os.path.join(image_dir, folder)))

    for entry in folders_to_delete:
        shutil.rmtree(entry[0], ignore_errors=True)
        shutil.rmtree(entry[1], ignore_errors=True)
        print(f"Deleted folder: {entry[0]} and {entry[1]}")

# Usage
labeled_dataset_path = r"C:\Users\K3000\Desktop\conversion test\old format"
formatted_dataset_path = r"C:\Users\K3000\Desktop\conversion test\mose_format"

generate_masks(labeled_dataset_path, formatted_dataset_path)
clean_folders(formatted_dataset_path)
