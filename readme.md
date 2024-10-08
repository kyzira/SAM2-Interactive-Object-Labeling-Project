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
        Uses *SAM2 Interface* script to display frames and allow user to manually select Objects
4. Segmentation with SAM2: Use SAM2 to segment the frames, saving the masks and the placed points in a single json file.
5. Labeling and json Creation: For each video, a single json file is created containing:
    - Which Frame this Observation belongs to
        - Which Damages the Frame has
            - How often the Damages appear on this frame
                - The polygon coordinates for every Mask per damage
                - The coordinates of the placed points


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

The ``yolo_integration.py`` script incorporates YOLO into the main workflow. Here’s how it works:

- YOLO is shown a random frame, where it tries to detect any objects.
- If objects are detected, the script gets the polygon coordinates and randomly selects points both inside and outside the segmentation.
- Only accept the prediction if confidence above 0.5, if multiple predictions appear, select the one with highest confidence score.
- These points are then fed into SAM2.
- This process repeats a few times (e.g., 5 rounds), after which SAM2 tracks the objects across all frames.


## Labeling Project

In this folder are the cut up frames, the masks and the placed points stored.

### Files

#### Current Index
The `current_index.txt` text file only contains a single number. It shows at which line the last labeling process stopped.

#### CSV List
The `.csv` list is used for the labeling process. It contains the damage type, where the video is located and when in the video the damage is visible.

### Folders

#### Results
The results are saved in the `results` folder. This folder contains a folder for every labeled video, in which is a json file with all the necessary information, and a folder where the cut frames are stored.

#### Avg Polygons
In this folder are txt files with coordinates. The name of the txt files corresponds to an Observation, and the coordinates inside are a representation of the average polygon shape of the observation. With these files it is possible to compare predicted shapes and

## Tabllen

The `.csv` Lists document damages, their video filepath, which damage they show and when in the video they were documented. These lists provide the Information needed for the Labeling Process.
