from ultralytics import YOLO
from sam2.build_sam import build_sam2_video_predictor  # type: ignore
import random
from shapely.geometry import Polygon, Point
import cv2
from PIL import Image
import torch
import os
import numpy as np


### LOADING MODELS ###

# Load SAM2
sam2_checkpoint = r"C:\Users\K3000\segment-anything-2\checkpoints\sam2_hiera_large.pt"
model_cfg = "sam2_hiera_l.yaml"

# Load YOLO model
model = YOLO(r"\\192.168.200.8\Datengrab\AI training YOLO\Yolo-3-Klassen-Training\Test 4 Finaler Datensatz\Segmentierung\best.pt")  # pretrained YOLOv8n model

# Use bfloat16 for the entire notebook
torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

if torch.cuda.get_device_properties(0).major >= 8:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)


### REST ###

def yolo_precheck(img_path, num_of_points):
    pos_points = []
    neg_points = []
    highest_conf = 0
    best_polygon = None

    # Load the image and check if successful
    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: Unable to read image at {img_path}")
        return pos_points, neg_points, highest_conf

    height, width = img.shape[:2]
    print(f"Processing image: {img_path}, Width: {width}, Height: {height}")

    try:
        # Get YOLO model results for the image
        results = model(img_path) 
    except Exception as e:
        print(f"Error in YOLO model prediction: {e}")
        return pos_points, neg_points, highest_conf

    # Process each result
    for result in results:
        try:
            masks = result.masks  # Segmentation masks
            confidences = result.boxes.conf.cpu().numpy()  # Confidence scores

            # Ensure confidences and masks are available
            if len(confidences) > 0 and masks and masks.xy:
                # Find the result with the highest confidence
                max_conf = np.max(confidences)
                if max_conf > highest_conf and max_conf > 0.5:
                    highest_conf = max_conf
                    # Get the corresponding mask for the highest confidence
                    polygon_coords = masks.xy[0]  # Get the first mask's coordinates

                    # Convert polygon coordinates to integer and create Polygon
                    integer_coords = [[int(round(x)), int(round(y))] for x, y in polygon_coords]
                    best_polygon = Polygon(integer_coords)  # Save the polygon for later
            elif not masks:
                while len(neg_points) < (num_of_points * 2):
                    random_point = Point(random.uniform(0, width), random.uniform(0, height))
                    neg_points.append((int(round(random_point.x)), int(round(random_point.y))))

        except Exception as e:
            print(f"Error processing result: {e}")

    # If a valid polygon was found, generate points
    if best_polygon is not None:
        min_x, min_y, max_x, max_y = best_polygon.bounds

        # Generate positive points inside the polygon
        while len(pos_points) < num_of_points:
            random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
            if best_polygon.contains(random_point):
                pos_points.append((int(round(random_point.x)), int(round(random_point.y))))

        # Generate negative points outside the polygon
        while len(neg_points) < num_of_points:
            random_point = Point(random.uniform(0, width), random.uniform(0, height))
            if not best_polygon.contains(random_point):
                neg_points.append((int(round(random_point.x)), int(round(random_point.y))))



    print(f"Generated {len(pos_points)} positive and {len(neg_points)} negative points.")
    return pos_points, neg_points, highest_conf


def show_propagated_images(mask_dir, inference_state, file_names):
    video_segments = {}

    for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state):
        video_segments[out_frame_idx] = {
            out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
            for i, out_obj_id in enumerate(out_obj_ids)
        }

    for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state, reverse=True):
        if out_frame_idx not in video_segments:
            video_segments[out_frame_idx] = {}
        for i, out_obj_id in enumerate(out_obj_ids):
            if out_obj_id not in video_segments[out_frame_idx]:
                video_segments[out_frame_idx][out_obj_id] = (out_mask_logits[i] > 0.0).cpu().numpy()
            else:
                video_segments[out_frame_idx][out_obj_id] = np.maximum(video_segments[out_frame_idx][out_obj_id], (out_mask_logits[i] > 0.0).cpu().numpy())

    os.makedirs(mask_dir, exist_ok=True)

    for out_frame_idx, masks in video_segments.items():
        for out_obj_id, out_mask in masks.items():
            out_mask = np.squeeze(out_mask)
            if out_mask.ndim == 2:
                original_file_name = os.path.splitext(file_names[out_frame_idx])[0]
                out_mask_img = Image.fromarray((out_mask * 255).astype('uint8'))
                out_mask_img.save(os.path.join(mask_dir, f'{original_file_name}.png'))
            else:
                print(f"Unexpected mask shape: {out_mask.shape}")


def save_points_to_txt(points, labels, frame, save_dir):
    txt_file = os.path.join(save_dir, f"{frame}.txt")
    with open(txt_file, 'w') as f:
        for point, label in zip(points, labels):
            x, y = point
            f.write(f"{int(x)}, {int(y)}, {int(label)}\n")

def save_confidence_to_txt(conf, frame, save_dir):
    txt_file = os.path.join(save_dir, f"{frame}_confidence.txt")

    # Write the confidence value to the file
    with open(txt_file, 'w') as f:
        f.write(str(conf))  # Write the confidence value as a string

def find_frame_index(frame, frame_dir):
    index = 0
    for file_name in os.listdir(frame_dir):
        if file_name.lower().endswith('.jpg'):
            if str(frame) in file_name:
                return index
            index += 1
    return None  # Return None if no match


def main(frame_dir=None):
    if frame_dir is None:
        frame_dir = r"C:\Users\K3000\Videos\SAM2 Tests\aaa_short"

    inference_state = predictor.init_state(video_path=frame_dir)
    mask_dir = os.path.join(frame_dir, "masks")

    os.makedirs(mask_dir, exist_ok=True)  # Create a directory to save the points if it doesn't exist

    ann_obj_id = 1
    num_input_frames = 7
    num_of_points = 12
    autobreak = 0
    file_list = [os.path.join(frame_dir, file_name) for file_name in os.listdir(frame_dir) if file_name.lower().endswith('.jpg')]
    file_names = [file_name for file_name in os.listdir(frame_dir) if file_name.lower().endswith('.jpg')]

    points_added = False  # Track if points were successfully added

    for _ in range(num_input_frames):
        pos_points = []
        neg_points = []
        autobreak = 0
        conf = 0

        while not (pos_points and neg_points) and autobreak < 4:
            img_path = random.choice(file_list)
            pos_points, neg_points, conf = yolo_precheck(img_path, num_of_points)
            autobreak += 1

        if not (pos_points and neg_points):
            continue

        points_added = True  # Points were successfully generated

        file_name = os.path.basename(img_path)
        frame = int(file_name.split(".")[0])
        frame_idx = find_frame_index(frame, frame_dir)

        if frame_idx is None:
            print(f"Frame {frame} not found in directory.")
            continue

        points_np = np.array(np.append(pos_points, neg_points, axis=0), dtype=np.float32)
        labels_np = np.array(np.concatenate((np.ones(len(pos_points)), np.zeros(len(neg_points))), axis=0), dtype=np.float32)

        predictor.add_new_points_or_box(
            inference_state=inference_state,
            frame_idx=frame_idx,
            obj_id=int(ann_obj_id),
            points=points_np,
            labels=labels_np
        )

        # Save the points to a .txt file with the frame number as the name
        save_points_to_txt(points_np, labels_np, frame, mask_dir)

        save_confidence_to_txt(conf, frame, frame_dir)

    if not points_added:
        print("No points were added. Skipping propagation.")
        return False  # No points to propagate, return False to skip to the next video

    show_propagated_images(mask_dir, inference_state, file_names)
    return True  # Return True to indicate successful processing



if __name__ == "__main__":
    main()
