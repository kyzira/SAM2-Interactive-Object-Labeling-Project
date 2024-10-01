from ultralytics import YOLO
from sam2.build_sam import build_sam2_video_predictor  # type: ignore
import random
from shapely.geometry import Polygon, Point
import cv2
from PIL import Image
import torch
import os
import numpy as np
from skimage import measure
from scipy.spatial import procrustes

### LOADING MODELS ###

# Load SAM2
sam2_checkpoint = r"C:\Users\K3000\sam2\checkpoints\sam2.1_hiera_large.pt"
model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"

# Load YOLO model
model = YOLO(r"\\192.168.200.8\Datengrab\AI training YOLO\Yolo-3-Klassen-Training\Test 4 Finaler Datensatz\Segmentierung\best.pt")  # pretrained YOLOv8n model

# Use bfloat16 for the entire notebook
torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

if torch.cuda.get_device_properties(0).major >= 8:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)


### REST ###

def yolo_precheck(img_path, num_of_points, schadens_kurzel):
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


    best_polygon = compare_with_sam(best_polygon, img_path, schadens_kurzel)        

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


def load_mean_shape_from_file(filepath):
    """
    Load the mean shape from a text file and return it as a numpy array.
    """
    mean_shape = []
    with open(filepath, 'r') as file:
        for line in file:
            x, y = map(float, line.strip().split(','))
            mean_shape.append((x, y))
    
    return np.array(mean_shape)


def compare_with_procrustes(polygon1, polygon2):
    """
    Compare two polygons using Procrustes analysis.
    Args:
        polygon1 (np.array): First polygon.
        polygon2 (np.array): Second polygon.
    
    Returns:
        float: Disparity score (lower is better).
    """
    _, _, disparity = procrustes(polygon1, polygon2)
    return disparity



def compare_with_sam(yolo_polygon, img_path, schadens_kurzel, threshold=0.02):
    """
    Compare YOLO polygon with SAM polygon from a mask, and if they differ, compare each to the mean shape.
    
    Args:
        yolo_polygon (list): Polygon from YOLO model (list of (x, y) points).
        img_path (str): Path to the image.
        mean_shape_path (str): Path to the text file containing the mean shape.
        threshold (float): Threshold for comparing YOLO and SAM polygons.
    
    Returns:
        list: Selected polygon (YOLO or SAM) based on comparison with the mean shape.
    """
    # Load the mean shape from file

    # Get directory and mask path
    img_dir = os.path.split(img_path)[0]
    mask_name = os.path.basename(img_path).replace(".jpg", ".png")
    mask_path = os.path.join(img_dir, "masks", mask_name)

    # If mask doesn't exist, return YOLO polygon
    if not os.path.exists(mask_path):
        return yolo_polygon

    # Load the SAM mask and find contours (polygons)
    mask = np.array(Image.open(mask_path).convert('1'))  # Convert to binary
    contours = measure.find_contours(mask, 0.5)

    if not contours:
        return yolo_polygon  # No contour found in SAM, fallback to YOLO polygon

    # Use the first contour as SAM's polygon (or apply any selection logic if multiple)
    sam_contour = np.flip(contours[0], axis=1)

    # Compare YOLO polygon with SAM polygon using Procrustes analysis
    yolo_polygon_np = np.array(yolo_polygon)
    sam_polygon_np = np.array(sam_contour)

    disparity_yolo_sam = compare_with_procrustes(yolo_polygon_np, sam_polygon_np)
    
    # If YOLO and SAM are similar enough, select YOLO polygon
    if disparity_yolo_sam <= threshold:
        return yolo_polygon
    
    temp_dir = os.path.dirname(os.path.dirname(img_dir))
    mean_shape_path = os.join.path(temp_dir, "avg polygons", f"{schadens_kurzel}_mean_shape.txt")

    mean_shape = load_mean_shape_from_file(mean_shape_path)
    
    # If YOLO and SAM differ, compare each with the mean shape
    disparity_yolo_mean = compare_with_procrustes(yolo_polygon_np, mean_shape)
    disparity_sam_mean = compare_with_procrustes(sam_polygon_np, mean_shape)
    
    # Return the polygon closer to the mean shape
    if disparity_yolo_mean < disparity_sam_mean:
        return yolo_polygon
    else:
        return sam_polygon_np.tolist()

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


def main(frame_dir=None, schadens_kurzel=None):
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
