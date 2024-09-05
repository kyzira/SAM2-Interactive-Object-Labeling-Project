from ultralytics import YOLO
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import random
from shapely.geometry import Polygon, Point
import cv2
from PIL import Image
import torch
import os
import numpy as np
import cv2


### LOADING MODELS ###

# Load SAM2
sam2_checkpoint = r"C:\Users\K3000\segment-anything-2\checkpoints\sam2_hiera_large.pt"
model_cfg = "sam2_hiera_l.yaml"


# Load YOLO model
model = YOLO(r"\\192.168.200.8\Datengrab\AI training YOLO\Yolo-3-Klassen-Training\Test 4 Finaler Datensatz\Segmentierung\best.pt")  # pretrained YOLOv8n model


# use bfloat16 for the entire notebook
torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

if torch.cuda.get_device_properties(0).major >= 8:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)


### REST ###

def yolo_precheck(img_path, num_of_points):
    pos_points = []
    neg_points = []

    height, width = cv2.imread(img_path).shape[:2]

    results = model(img_path)  # return a list of Results objects

    # Process results list
    for result in results:
        masks = result.masks  # Masks object for segmentation masks outputs

        if masks and masks.xy:
            polygon_coords = masks.xy[0]  # Get the first mask's coordinates

            integer_coords = [[int(round(x)), int(round(y))] for x, y in polygon_coords]
            
            polygon = Polygon(integer_coords)
            min_x, min_y, max_x, max_y = polygon.bounds

            while len(pos_points) < num_of_points:
                # Generate random points within the bounding box
                random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
                
                # Check if the point is inside the polygon
                if polygon.contains(random_point):
                    pos_points.append((int(round(random_point.x)), int(round(random_point.y))))  # Add point to the list

            while len(neg_points) < num_of_points:
                # Generate random points within the bounding box
                random_point = Point(random.uniform(0, width), random.uniform(0, height))
                
                # Check if the point is outside the polygon
                if not polygon.contains(random_point):
                    neg_points.append((int(round(random_point.x)), int(round(random_point.y))))  # Add point to the list

        # result.show()  # display to screen
        # result.save(filename="result.jpg")  # save to disk

    return pos_points, neg_points

def show_propagated_images(mask_dir, inference_state):
    # Run propagation throughout the video and collect the results in a dict
    video_segments = {}  # video_segments contains the per-frame segmentation results
    
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
                # Optionally merge or update masks if needed
                video_segments[out_frame_idx][out_obj_id] = np.maximum(video_segments[out_frame_idx][out_obj_id], (out_mask_logits[i] > 0.0).cpu().numpy())


    os.makedirs(mask_dir,exist_ok=True)

    for out_frame_idx, masks in video_segments.items():
        for out_obj_id, out_mask in masks.items():
            # Remove singleton dimensions
            out_mask = np.squeeze(out_mask)  # Squeeze to remove dimensions of size 1

            # Convert the mask to a PIL image
            if out_mask.ndim == 2:  # If the mask is 2D, proceed
                out_mask_img = Image.fromarray((out_mask * 255).astype('uint8'))
                # Save the mask image with an increasing index
                out_mask_img.save(os.path.join(mask_dir, f'{out_frame_idx:05d}.png'))
            else:
                    print(f"Unexpected mask shape: {out_mask.shape}")

def find_frame_index(frame, frame_dir):
    index = 0
    for file_name in os.listdir(frame_dir):
        file_path = os.path.join(frame_dir, file_name)
        if file_path.lower().endswith('.jpg'):
            if str(frame) in file_name:
                return index
            else:
                index += 1


def main():

    frame_dir = r"C:\Users\K3000\Videos\SAM2 Tests\aaa_short"    

    inference_state = predictor.init_state(video_path=frame_dir)
    mask_dir = os.path.join(frame_dir, "masks")

    ann_obj_id = 1

    num_input_frames = 7 # Num of Frames
    num_of_points = 12 # Num of Points per Frame


    file_list = []

    for file_name in os.listdir(frame_dir):
        file_path = os.path.join(frame_dir, file_name)
        if file_path.lower().endswith('.jpg'):
            file_list.append([file_path, file_name])


    for _ in range(num_input_frames):

        pos_points = []
        neg_points = []
        autobreak = 0
        file_name = ""

        while not (pos_points and neg_points):
            img_path, file_name = random.choice(file_list)
            pos_points, neg_points = yolo_precheck(img_path, num_of_points)
            if autobreak > 5:
                break
        
        frame = int(file_name.split(".")[0])
        frame_idx = find_frame_index(frame, frame_dir)

        if (pos_points and neg_points):
            points_np = np.array(np.append(pos_points, neg_points, axis=0), dtype=np.float32)
            # Ensure the length of labels matches the number of points
            labels_np = np.array(np.concatenate((np.ones(len(pos_points)), np.zeros(len(neg_points))), axis=0), dtype=np.float32)
        else:
            continue


        print(points_np)

        _, _, _ = predictor.add_new_points_or_box(
            inference_state=inference_state,
            frame_idx=frame_idx,
            obj_id=int(ann_obj_id),
            points=points_np,
            labels=labels_np
        )


    print("Points Inside Polygon:", pos_points)
    print("Points Outside Polygon:", neg_points)

    show_propagated_images(mask_dir, inference_state)





if __name__ == "__main__":
    main()