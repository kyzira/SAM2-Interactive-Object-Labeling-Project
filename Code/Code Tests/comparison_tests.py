import os
import numpy as np
from PIL import Image
from skimage import measure
from scipy.spatial import procrustes
from shapely.geometry import Polygon, Point
from shapely.geometry.polygon import LinearRing

def resample_polygon(polygon, num_points=100):
    """
    Resample a polygon to have a fixed number of points.
    
    Args:
        polygon (list of tuples): List of (x, y) coordinates representing the polygon.
        num_points (int): The desired number of points.
        
    Returns:
        np.array: Resampled polygon with num_points (x, y) coordinates, or None if invalid.
    """
    try:
        poly = Polygon(polygon)
        if not poly.is_valid or poly.is_empty:
            raise ValueError("Invalid or empty polygon.")
        
        # Convert polygon to a LinearRing to get a continuous perimeter
        ring = LinearRing(poly.exterior.coords)
        
        # Get equally spaced points along the perimeter
        distances = np.linspace(0, ring.length, num_points)
        resampled_coords = [ring.interpolate(distance).coords[0] for distance in distances]
        
        return np.array(resampled_coords)
    
    except Exception as e:
        print(f"Error resampling polygon: {e}")
        return None

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
    try:
        _, _, disparity = procrustes(polygon1, polygon2)
        return disparity
    except ValueError as e:
        print(f"Error comparing polygons with Procrustes: {e}")
        return float('inf')  # Return a large disparity if comparison fails

def compare_with_sam(yolo_polygon, img_path, mean_shape_path, threshold=0.02, num_points=100):
    """
    Compare YOLO polygon with SAM polygon from a mask, and if they differ, compare each to the mean shape.
    
    Args:
        yolo_polygon (list): Polygon from YOLO model (list of (x, y) points).
        img_path (str): Path to the image.
        mean_shape_path (str): Path to the text file containing the mean shape.
        threshold (float): Threshold for comparing YOLO and SAM polygons.
        num_points (int): Number of points to resample polygons to.
    
    Returns:
        list: Selected polygon (YOLO or SAM) based on comparison with the mean shape.
    """
    # Load the mean shape from file
    mean_shape = load_mean_shape_from_file(mean_shape_path)
    
    # Get directory and mask path
    img_dir = os.path.split(img_path)[0]
    mask_name = os.path.basename(img_path).replace(".jpg", ".png")
    mask_path = os.path.join(img_dir, "masks", mask_name)

    # If mask doesn't exist, return YOLO polygon
    if not os.path.exists(mask_path):
        print(f"Mask not found for image: {img_path}")
        return yolo_polygon

    # Load the SAM mask and find contours (polygons)
    mask = np.array(Image.open(mask_path).convert('1'), dtype=np.uint8)  # Ensure binary mask
    contours = measure.find_contours(mask, 0.5)
    
    if not contours:
        print(f"No contours found in SAM mask for image: {img_path}")
        return yolo_polygon  # No contour found in SAM, fallback to YOLO polygon
    
    # Use the first contour as SAM's polygon (or apply any selection logic if multiple)
    sam_contour = np.flip(contours[0], axis=1)
    
    # Resample YOLO and SAM polygons to have the same number of points
    yolo_polygon_resampled = resample_polygon(yolo_polygon, num_points)
    sam_polygon_resampled = resample_polygon(sam_contour, num_points)
    
    if yolo_polygon_resampled is None or sam_polygon_resampled is None:
        return yolo_polygon  # Fallback to YOLO polygon if resampling failed

    # Compare YOLO polygon with SAM polygon using Procrustes analysis
    disparity_yolo_sam = compare_with_procrustes(yolo_polygon_resampled, sam_polygon_resampled)
    
    # If YOLO and SAM are similar enough, select YOLO polygon
    if disparity_yolo_sam <= threshold:
        print(f"YOLO and SAM polygons are similar (disparity: {disparity_yolo_sam}). Selecting YOLO polygon.")
        return yolo_polygon

    # Resample mean shape to the same number of points
    mean_shape_resampled = resample_polygon(mean_shape, num_points)
    
    # Compare each with the mean shape
    disparity_yolo_mean = compare_with_procrustes(yolo_polygon_resampled, mean_shape_resampled)
    disparity_sam_mean = compare_with_procrustes(sam_polygon_resampled, mean_shape_resampled)
    
    # Print disparity for debugging
    print(f"Disparity YOLO vs SAM: {disparity_yolo_sam}")
    print(f"Disparity YOLO vs Mean: {disparity_yolo_mean}")
    print(f"Disparity SAM vs Mean: {disparity_sam_mean}")
    
    # Return the polygon closer to the mean shape
    if disparity_yolo_mean < disparity_sam_mean:
        print(f"YOLO polygon is closer to the mean shape. Selecting YOLO polygon.")
        return yolo_polygon
    else:
        print(f"SAM polygon is closer to the mean shape. Selecting SAM polygon.")
        return sam_polygon_resampled.tolist()

# Example usage
yolo_polygon = [(100, 200), (150, 200), (150, 250), (100, 250)]  # Replace with actual YOLO output
img_path = r"C:\Code Python\automation-with-sam2\labeling_project\masks\F416Q33076060A.MPG\15450.jpg"  # Path to the current image
mean_shape_path = r"C:\Code Python\automation-with-sam2\labeling_project\avg polygons\BABAA_mean_shape.txt"  # Path to the precomputed mean shape

selected_polygon = compare_with_sam(yolo_polygon, img_path, mean_shape_path)
print(f"Selected polygon: {selected_polygon}")
