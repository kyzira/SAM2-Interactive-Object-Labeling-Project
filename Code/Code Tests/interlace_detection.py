import cv2
import numpy as np

# Video laden
video = cv2.VideoCapture(r"C:\Users\K3000\Videos\SAM2 Tests\test.mp4")
counter = 0
while True:
    ret, frame = video.read()
    if not ret:
        break

    # Unterschiede zwischen Zeilen analysieren
    interlace_artifacts = np.sum(abs(frame[::2, :] - frame[1::2, :]))

    if interlace_artifacts > 6000000:  # Schwellwert
        counter += 1
        
print(f"Interlacing erkannt bei {counter} frames!")

video.release()
