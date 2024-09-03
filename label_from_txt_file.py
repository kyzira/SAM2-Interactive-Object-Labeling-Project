from PIL import Image
import torch
import os
import numpy as np
from sam2.build_sam import build_sam2_video_predictor # type: ignore

# Initialize the predictor
sam2_checkpoint = r"C:\Users\K3000\segment-anything-2\checkpoints\sam2_hiera_large.pt"
model_cfg = "sam2_hiera_l.yaml"

# Use bfloat16 for the entire notebook
torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

if torch.cuda.get_device_properties(0).major >= 8:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

frame_dir = r"C:\Users\K3000\Videos\SAM2 Tests\KI_1"
ann_obj_id = 1

predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)

inference_state = predictor.init_state(video_path=frame_dir)

mask_dir = os.path.join(frame_dir, "masks")

def show_propagated_images():
    # Run propagation throughout the video and collect the results in a dict
    video_segments = {}  # video_segments contains the per-frame segmentation results
    
    for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state):
        video_segments[out_frame_idx] = {
            out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
            for i, out_obj_id in enumerate(out_obj_ids)
        }

    os.makedirs(os.path.join(mask_dir,"mask_ony_with_txt"),exist_ok=True)

    for out_frame_idx, masks in video_segments.items():
        for out_obj_id, out_mask in masks.items():
            # Remove singleton dimensions
            out_mask = np.squeeze(out_mask)  # Squeeze to remove dimensions of size 1

            # Convert the mask to a PIL image
            if out_mask.ndim == 2:  # If the mask is 2D, proceed
                out_mask_img = Image.fromarray((out_mask * 255).astype('uint8'))
                # Save the mask image with an increasing index
                out_mask_img.save(os.path.join(mask_dir,"mask_ony_with_txt", f'{out_frame_idx:05d}.png'))
            else:
                    print(f"Unexpected mask shape: {out_mask.shape}")



for file_name in os.listdir(mask_dir):
    file_path = os.path.join(mask_dir, file_name)
    
    if file_path.lower().endswith('.txt'):
        # Read points and labels from .txt file
        points = []
        labels = []
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    x, y, label = float(parts[0].strip()), float(parts[1].strip()), int(parts[2].strip())
                    points.append((x, y))
                    labels.append(label)
        
        points_np = np.array(points, dtype=np.float32)
        labels_np = np.array(labels, dtype=np.float32)

        # Extract frame index from file_name
        frame_idx = int(file_name.split(".")[0])
        
        _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(
            inference_state=inference_state,
            frame_idx=frame_idx,
            obj_id=int(ann_obj_id),
            points=points_np,
            labels=labels_np
        )
    
show_propagated_images()


