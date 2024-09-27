# This is to test, how to output the confidence score and to raise a flag if it is below a certain degree

from ultralytics import YOLO
import cv2
import random
from shapely.geometry import Polygon, Point
import cv2
from PIL import Image
import torch
import os
import numpy as np


# Load YOLO model
model = YOLO(r"\\192.168.200.8\Datengrab\AI training YOLO\Yolo-3-Klassen-Training\Test 4 Finaler Datensatz\Segmentierung\best.pt")  # pretrained YOLOv8m model

def yolo_precheck(img_path, num_of_points):
    pos_points = []
    neg_points = []
    conf = 0

    height, width = cv2.imread(img_path).shape[:2]

    results = model(img_path)  # return a list of Results objects

    # Process results list
    for result in results:
        masks = result.masks  # Masks object for segmentation masks outputs
        #conf = result.boxes.conf.cpu().numpy()
        print("Results:")
        print(result)
        print("Result Finished")

        if masks and masks.xy:
            polygon_coords = masks.xy[0]  # Get the first mask's coordinates

            integer_coords = [[int(round(x)), int(round(y))] for x, y in polygon_coords]
            polygon = Polygon(integer_coords)
            min_x, min_y, max_x, max_y = polygon.bounds

            while len(pos_points) < num_of_points:
                random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
                if polygon.contains(random_point):
                    pos_points.append((int(round(random_point.x)), int(round(random_point.y))))

            while len(neg_points) < num_of_points:
                random_point = Point(random.uniform(0, width), random.uniform(0, height))
                if not polygon.contains(random_point):
                    neg_points.append((int(round(random_point.x)), int(round(random_point.y))))

    return pos_points, neg_points, conf


img_path = r"C:\Code Python\automation-with-sam2\labeling_project\masks\F416Q33076060A.MPG\15450.jpg"

_, _, conf = yolo_precheck(img_path, 1)


print("\nConfidence:")
print(conf)