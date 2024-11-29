import cv2
import numpy as np

def deblur_image(image_path, output_path, kernel_size=15):
    image = cv2.imread(image_path)
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size-1)/2), :] = np.ones(kernel_size)
    kernel /= kernel_size
    
    # Apply Wiener filter approximation
    deblurred = cv2.filter2D(image, -1, kernel)
    cv2.imwrite(output_path, deblurred)

# Example usage
deblur_image(r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\Code\Code Tests\02700.jpg", "deblurred_frame.jpg")