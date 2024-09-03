# SAM2 Interactive Object Labeling Project
This project provides an interactive interface for labeling objects using SAM2. Before using SAM2, a video must be converted into individual frames, which can then be processed and labeled.

## Convert Video to Frames
To convert a video into frames, use the convert_video_to_frames.py script. This script extracts frames from the video and saves them in a separate folder within the same directory as the original video file. You can specify the start and end frames, as well as the interval at which frames are saved.


## SAM2 Interface
The sam2_interface.py script provides a user-friendly interface to display and segment the extracted frames. The frames are shown in a grid layout, and you can navigate through them using a slider.

Clicking on a specific frame opens it in a separate window, where you can interactively label the object by adding positive and negative points using left and right clicks. If needed, you can undo the last point with the backspace key. Once you're satisfied with the selection and close the window, the segmentation will be applied to all subsequent frames automatically.

If the segmentation result in any frame isn't satisfactory, you can revisit it and add more points to improve the accuracy.