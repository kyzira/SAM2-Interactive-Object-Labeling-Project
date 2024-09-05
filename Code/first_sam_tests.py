import cv2
import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk
from PIL import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import re

# use bfloat16 for the entire notebook
torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

if torch.cuda.get_device_properties(0).major >= 8:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

sam2_checkpoint = r"C:\Users\K3000\segment-anything-2\checkpoints\sam2_hiera_large.pt"
model_cfg = "sam2_hiera_l.yaml"

# create the predictor object
predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)

def convert_video():
    input_path = input("Video Path (without quotes): ").strip()
    path_splits = os.path.normpath(input_path).split(os.path.sep)
    base_name = os.path.splitext(path_splits[-1])[0]
    input_dir = os.path.dirname(input_path)
    frame_dir = os.path.join(input_dir, f"{base_name}")
    output_dir = os.path.join(input_dir, f"{base_name}_result")
    os.makedirs(frame_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file: {input_path}")
        return
    print("Successfully opened the video! \nSaving frames:")
    frame_number = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        output_filename = os.path.join(frame_dir, f'{frame_number:05d}.jpg')
        cv2.imwrite(output_filename, frame)
        frame_number += 1
    cap.release()
    print(f"Frames have been saved to {frame_dir}.")
    return frame_dir, output_dir, input_path


def show_video_with_pause(input_path):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file: {input_path}")
        return
    cv2.waitKey(1500)
    frame_number = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Video Playback', frame)
        key = cv2.waitKey(30)
        if key == ord(' '):
            add_points(frame_number, os.path.join(frame_dir,f"{frame_number:05d}.jpg"))
        elif key == 27:
            break
        frame_number += 1
    cap.release()
    cv2.destroyAllWindows()


def add_points(frame_number, image_path):
    ann_frame_idx = frame_number
    ann_obj_id = input("Input Object ID: ")

    # Initialize lists to store points and labels
    points = []
    labels = []

    def on_click(event):
        # Get the click coordinates relative to the image
        ix, iy = int(event.x), int(event.y)
        if event.num == 1:
            print(f"Left click at ({ix}, {iy}) - 1")
            points.append([ix, iy])
            labels.append(1)
        elif event.num == 3:
            print(f"Right click at ({ix}, {iy}) - 0")
            points.append([ix, iy])
            labels.append(0)
        update_mask()

    def on_key_press(event):
        nonlocal points, labels
        if event.keysym == "BackSpace":
            if points:
                points.pop()
                labels.pop()
                update_mask()
        elif event.keysym == "Return":
            print("Enter pressed")
            show_propagated_images()
            

    def update_mask():
        if points and labels:
            points_np = np.array(points, dtype=np.float32)
            labels_np = np.array(labels, dtype=np.int32)
            _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(
                inference_state=inference_state,
                frame_idx=ann_frame_idx,
                obj_id=int(ann_obj_id),
                points=points_np,
                labels=labels_np,
            )


            mask = (out_mask_logits[0] > 0.0).squeeze().cpu().numpy().astype(np.uint8) * 255
            
            # Speichere die Maske als Bilddatei
            mask_image = Image.fromarray(mask)
            mask_image.save(os.path.join(output_dir, f'mask_{ann_frame_idx:05d}.png'))

            # Clear previous plot and update the mask
            ax.clear()
            ax.imshow(image, aspect='auto')
            ax.axis('off')  # Ensure axes are completely off
            show_points(points_np, labels_np, ax)
            show_mask((out_mask_logits[0] > 0.0).cpu().numpy(), ax, obj_id=out_obj_ids[0])
            canvas.draw()

    # Create the main window
    root = Tk()
    root.title("Image Viewer")

    image = Image.open(image_path)

    # Create a matplotlib figure and axis for displaying predictions
    fig = plt.figure(figsize=(image.width / 100, image.height / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])  # Use the entire figure
    ax.imshow(image)
    ax.axis('off')  # Turn off axes completely

    # Create a Canvas widget to integrate matplotlib with Tkinter
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=1)

    # Bind mouse click events to the canvas
    canvas.get_tk_widget().bind("<Button-1>", on_click)  # Left click
    canvas.get_tk_widget().bind("<Button-3>", on_click)  # Right click
    canvas.get_tk_widget().bind("<KeyPress>", on_key_press)  # Key press for Backspace

    # Start the Tkinter event loop
    root.mainloop()

def show_propagated_images(n=25):
    # Run propagation throughout the video and collect the results in a dict
    video_segments = {}  # video_segments contains the per-frame segmentation results
    
    for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state):
        # Skip frames that are not every n-th frame
        if out_frame_idx % n != 0:
            continue
        
        video_segments[out_frame_idx] = {
            out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
            for i, out_obj_id in enumerate(out_obj_ids)
        }

    # Render and save the segmentation results only for the propagated frames
    plt.close("all")
    result_dir = os.path.join(output_dir, "propagated_frames")
    os.makedirs(result_dir, exist_ok=True)  # Create the directory if it doesn't exist

    for out_frame_idx in sorted(video_segments.keys()):
        plt.figure(figsize=(6, 4))
        plt.axis('off')  # Remove axes
        plt.imshow(np.zeros_like(Image.open(os.path.join(frame_dir, frame_names[out_frame_idx]))))  # Display a black background
        
        for out_obj_id, out_mask in video_segments[out_frame_idx].items():
            show_mask(out_mask, plt.gca(), obj_id=out_obj_id)
        
        # Save the mask image with an increasing index
        plt.savefig(os.path.join(result_dir, f'{out_frame_idx:05d}.png'), bbox_inches='tight', pad_inches=0)
        plt.clf()  # Clear the figure to prevent overlapping of images




def show_mask(mask, ax, obj_id=None, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        cmap = plt.get_cmap("tab10")
        cmap_idx = 0 if obj_id is None else obj_id
        color = np.array([*cmap(cmap_idx)[:3], 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image, alpha=0.5)

def show_points(coords, labels, ax, marker_size=200):
    pos_points = coords[labels==1]
    neg_points = coords[labels==0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)

def show_box(box, ax):
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green', facecolor=(0, 0, 0, 0), lw=2))

def create_video_from_images(image_dir, output_video_dir, fps=24):
    # Get the list of all image filenames in the directory
    image_files = sorted([f for f in os.listdir(image_dir) if re.match(r'\d{5}\.png', f)])
    output_video_path = os.path.join(output_video_dir, "video.mp4")
    
    if not image_files:
        print("No images found in the directory!")
        return
    
    # Get the dimensions of the first image
    first_image_path = os.path.join(image_dir, image_files[0])
    frame = cv2.imread(first_image_path)
    height, width, layers = frame.shape

    # Define the codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # 'mp4v' for .mp4 output
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Iterate over each file and add it to the video
    for image_file in image_files:
        image_path = os.path.join(image_dir, image_file)
        frame = cv2.imread(image_path)
        
        if frame is None:
            print(f"Warning: {image_file} could not be read. Skipping.")
            continue
        
        video.write(frame)

    # Release the video writer object
    video.release()
    print(f"Video saved as {output_video_path}")




# Run the function
#frame_dir, output_dir, input_path = convert_video()
frame_dir = r"C:\Users\K3000\Videos\aaa"
input_path = r"C:\Users\K3000\Videos\aaa.mp4"
output_dir = r"C:\Users\K3000\Videos\aaa_result"

# Betrachte jeden {faktor}-ten frame
faktor = 1



inference_state = predictor.init_state(video_path=frame_dir)

frame_names = [
    p for p in os.listdir(frame_dir)
    if os.path.splitext(p)[-1] in [".jpg", ".jpeg", ".JPG", ".JPEG"]
]
frame_names.sort(key=lambda p: int(os.path.splitext(p)[0]))

show_video_with_pause(input_path)





# Run propagation throughout the video and collect the results in a dict
video_segments = {}  # video_segments contains the per-frame segmentation results
for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state):
    video_segments[out_frame_idx] = {
        out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
        for i, out_obj_id in enumerate(out_obj_ids)
    }
    print(f"Processed frame index: {out_frame_idx}")

# Render the segmentation results every few frames



fps = 24/faktor
vis_frame_stride = faktor
plt.close("all")

result_dir = os.path.join(output_dir, "frames")
os.makedirs(result_dir, exist_ok=True)  # This will create the directory if it doesn't already exist

# Define the figure outside of the loop
fig = plt.figure(figsize=(6, 4))
for out_frame_idx in range(0, len(frame_names), vis_frame_stride):
    if out_frame_idx not in video_segments:
        print(f"Frame index {out_frame_idx} is missing in video_segments")
        continue

    plt.title(f"frame {out_frame_idx}")
    im = plt.imshow(Image.open(os.path.join(frame_dir, frame_names[out_frame_idx])), animated=True)
    for out_obj_id, out_mask in video_segments[out_frame_idx].items():
        show_mask(out_mask, plt.gca(), obj_id=out_obj_id)

    # Save the files with an increasing index in the folder called output
    plt.savefig(os.path.join(result_dir, f'{out_frame_idx:05d}.png'))
    plt.clf()  # Clear the figure to prevent overlapping of images

create_video_from_images(result_dir, output_dir, fps)