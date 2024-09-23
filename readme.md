# SAM2 Interactive Object Labeling Project

This project provides a streamlined, interactive interface for object labeling using SAM2. The process begins with converting a video into individual frames, which are then processed and labeled.

## Code

`main_loop.py`:

Pay attention to the ``auto_label`` boolean. If set to ``True``, Frames of the video will be labeld using the pretrained YOLO model, if set to ``False`` the frames will be shown to the user. Depending on its state different scripts will be used.

Flow of `main_loop.py`:

1. Directory Setup: Initialize the necessary directories and load the damage table and index.
2. Video Processing: Load the video and cut it into frames based on the specified timeslot.
3. Depending on state of `auto_label`:
    - ``auto_label = True``:
        Detect Objects and set Points using *YOLO Integration* script
    - ``auto_label = False``:
        Use *SAM2 Interface* script to display frames and allow user to manually select Objects
4. Segmentation with SAM2: Use SAM2 to segment the frames, saving the masks and associated .txt files with the labeled points.
5. Labeling and CSV Creation: For each damage, create a .csv file containing:
    - Damage Type: Type of damage observed.
    - Start and End Frames: The first and last frames where the damage is visible.
    - Point Frame: The specific frame where a labeling point was placed.
    - Coordinates: The X and Y coordinates of the labeled point.
    - Label: The label assigned (0 or 1).

### Scripts

#### Convert Video to Frames

The ``convert_video_to_frames.py`` script extracts frames from a video and saves them in a designated folder within the same directory as the original video file. Key features include:

- Custom Frame Selection: Specify start and end frames, and define the interval for frame extraction.
- Automatic Frame Calculation: Input the timestamp of the damage occurrence, and the script will automatically calculate and extract the relevant frames before and after the event.

#### SAM2 Interface

The ``sam2_interface.py`` script provides an intuitive interface for displaying and segmenting the extracted frames. Key functionalities include:

- Grid Layout: Frames are displayed in a grid, allowing easy navigation using a slider.
- Interactive Labeling: Click on a specific frame to open it in a separate window, where you can add positive and negative points for labeling using left and right clicks.
- Undo Feature: Use the backspace key to remove the last point if needed.
- Automated Segmentation: After labeling, segmentation is applied automatically to all subsequent frames.
- Refinement Option: Revisit any frame to add more points and improve segmentation accuracy if needed.

#### YOLO Integration

The ``test_yolo_integration.py`` script incorporates YOLO into the main workflow. Here’s how it works:

- YOLO is shown a random frame, where it tries to detect any objects.
- If objects are detected, the script gets the polygon coordinates and randomly selects points both inside and outside the segmentation.
- These points are then fed into SAM2.
- This process repeats a few times (e.g., 5 rounds), after which SAM2 tracks the objects across all frames.

#### Display Images with Mask

The `display_images_with_mask.py` script displays a grid with images from a selectable directory with the corresponding masks laid over the images.

## Labeling Project

In this folder are the cut up frames, the masks and the generated points stored.

## CSV Lists

The `.csv` Lists document damages, their video filepath, which damage they show and when in the video they were documented. These lists provide the Information needed for the Labeling Process.
