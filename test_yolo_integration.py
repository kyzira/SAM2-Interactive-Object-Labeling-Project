from ultralytics import YOLO

# Load a model
model = YOLO(r"\\192.168.200.8\Datengrab\AI training YOLO\Yolo-3-Klassen-Training\Test 4 Finaler Datensatz\Segmentierung\best.pt")  # pretrained YOLOv8n model

# Run batched inference on a list of images
results = model(r"C:\Users\K3000\Pictures\Random Damage Images\_6044D08195353__.mpg.19050_DAMAGE.jpg")  # return a list of Results objects

# Process results list
for result in results:
    boxes = result.boxes  # Boxes object for bounding box outputs
    masks = result.masks  # Masks object for segmentation masks outputs
    print(masks.xy)
    keypoints = result.keypoints  # Keypoints object for pose outputs
    probs = result.probs  # Probs object for classification outputs
    obb = result.obb  # Oriented boxes object for OBB outputs
    result.show()  # display to screen
    result.save(filename="result.jpg")  # save to disk