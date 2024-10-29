from ultralytics.data.annotator import auto_annotate

# auto_annotate(data=r"C:\Users\K3000\Videos\SAM2 Tests\whole video", det_model=r"C:\Code Python\Yolo-Training-Rohrerkennung\Test 3\Segmentation\runs\segment\train\weights\best.pt", sam_model='sam2.1_l.pt')

import cv2
import numpy as np
import os

def draw_segmentation(image, label_path, class_names):
    height, width, _ = image.shape

    with open(label_path, 'r') as f:
        for line in f.readlines():
            label = line.strip().split()
            class_id = int(label[0])
            num_points = (len(label) - 1) // 2
            points = []

            for i in range(num_points):
                x = float(label[1 + 2 * i]) * width
                y = float(label[2 + 2 * i]) * height
                points.append([int(x), int(y)])

            points = np.array([points], dtype=np.int32)
            cv2.polylines(image, [points], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.putText(image, class_names[class_id], (points[0][0][0], points[0][0][1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.fillPoly(image, [points], color=(0, 255, 0, 50))

    return image

# Ordnerpfade
frames_folder = r"C:\Users\K3000\Videos\SAM2 Tests\whole video"
labels_folder = r"C:\Users\K3000\Videos\SAM2 Tests\whole video_auto_annotate_labels"
output_folder = r"C:\Users\K3000\Videos\SAM2 Tests\mit maske"
os.makedirs(output_folder, exist_ok=True)

# Klassenliste
class_names = ['Anschluss', 'Riss', 'Wurzel']

# Verarbeite jedes Frame und zugehöriges Label
for frame_name in sorted(os.listdir(frames_folder)):
    frame_path = os.path.join(frames_folder, frame_name)
    label_path = os.path.join(labels_folder, frame_name.replace('.jpg', '.txt'))  # Annahme: Labels haben denselben Namen wie Frames
    
    if os.path.exists(label_path):
        image = cv2.imread(frame_path)
        image_with_segmentation = draw_segmentation(image, label_path, class_names)
        
        # Ergebnis speichern
        output_path = os.path.join(output_folder, frame_name)
        cv2.imwrite(output_path, image_with_segmentation)
