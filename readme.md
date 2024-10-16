# SAM2 Interactive Object Labeling Project

This project provides a streamlined, interactive interface for object labeling using SAM2. The process begins with converting a video into individual frames, which are then processed and labeled and finally saved in a json.

## Workflow

### **Label using a list**
1. Load the damage list and the current index while checking the start options.
2. Retrieve video information, damage timestamp, and damage type from the damage list at the current index.
3. Extract frames from the video based on the damage timestamp.
4. Start the labeling process, which depends on the auto_labeling variable.

### **Display Folder**
The application allows you to display and interact with the labeled frames through a user-friendly interface.

## Folder Structure

### **Code**
---
#### **Main**
The Main Function ``main.py`` serves as an entry point for this project. 

##### Workflow
1. Load the *damage list*, the *current index* and check the start options
2. Get *video information*, *damage time stamp* and *damage type* from the *damage list* at the *current index*
3. Extract frames from the video
4. Start labeling process depending on ``auto_labeling`` variable

Key Configuration Variables:
- ``auto_labeling``: For more info, look at the correspoding chapters.
    - ``auto_labeling = True``: Start labeling automatically using the **Yolo Sam cooperation** Module.
    - ``auto_labeling = False``: Start labeling manually using the **Main Window** Module.
- ``test_mode``
    - ``test_mode = True``: Activates test mode, doesnt loop through the list, opens ``test folder`` in the ``labeling_project`` folder
    - ``test_mode = False``: Normal operation
- ``watch_mode``: To be added
- ``frame_rate``: Defines in what rate frames are extracted from the Video.
- ``output_dir``: This is the Directory in which a ``results`` Folder will be saved. For every Processed video a new folder will be created inside the ``results`` folder.
- ``table_path``: This is the path to the csv, in which all Observations are stored
    
##### Test Mode
If the ``test_mode`` variable is set to *True* the test mode will activate.
The main code wont loop over the given table and instead will open a predetermined folder in ``labeling_project/test folder``

#### **Main Window**
The Main Window displays a *tkinter* window, in which all extracted frames are visible. 
Here you can:
- display the images
- display the masks for these images, if there are any
- Add, remove or change the observations
- Extract more images, either before the shown images, or after them

##### Workflow
1. Select desired observation from the Radio Button list. 
    - If the selected Observation is not in the list, you can add it with the entry field to its left
2. Click on any Image, in which the selected observation is visible.
    - **Annotation Window** will open, follow its directions to segment your observation.
3. After the segmentation is finished and the **Annotation Window** closed, tracking throughout the whole video will begin. When its finished, masks for all images will be displayed.
4. If unsatisfied with a mask, just click on the image and re-segment it inside **Annotation Window**. After closing, all segmentations will adapt.
5. Want to segment an other observation? Just switch to it with the Radio Buttons and start at **2.** All observations will be displayed in different colors.

#### **Annotation Window**
The Annotation Window is where segmentation is performed. Users can interact with the interface to draw masks around the identified objects or areas of interest.
Workflow:
- **Left Click**:
    Adds a positive Point to the clicked coordinates. A positive Point dictates to SAM that the Object you want to track is in the clicked position
- **Right Click**:
    Adds a negative Point to the clicked coordinates. A negative Point dictates to SAM that the Object you want to track is definetly not in the clicked position
- **Backspace Key**:
    Removes last added Point
- **Close Window**:
    Finishes the annotation process.
- **get_points_and_labels**:
    This method can be called from outside this module. It will return a list of the clicked coordinates, a list wether those clicks were positive or negative points and the polygons for the current image.
    These lists can then be used to track the object throughout the whole video.

#### **SAM2 Class**
Here will SAM2 be initialized. This class helps interacting with SAM2 own API. 
It is necessary to put in the path to your local SAM2 model. The Input parameter is the directory, in which the to be tracked frames are stored.

The usable functions are:
- **Add Points**:
    Points are added to SAM for a singular Image. Used in **Annotation Window**. It returns the Mask for that image
- **Propagate in Video**:
    Only usable if Points were added prior. When this function is called, all frames in the directory are tracked originating from the first image, in which you selected the observation

#### **Json Read Write**
This Class is used to interact with the json file. It helps storing the observations in a structured way.
With ``add_frame_to_json`` it is possible to add all the info necessary for recreating and further using the mask to the json.

#### **Extract Frames from Video**
This module is used to extract Frames from the input video. The time slot, of which frames are extracted can be given either through the time stamp or the exact frames, from start to end.

#### **Further Extract Frames**
This is used, when inside the Main Window, the extract more frames buttons are clicked. This pulls up the video, and extracts a set amount of frames in either direction

#### **Frame Info Struct**
This Class is a Struct like class. It is used to store multiple paths, directories and the frames opened as PIL Images for easy access.

#### **Observation Management**
This Class is used to store the observations list, to add and to remove from it.

#### **Yolo Sam cooperation**
To be added

### **Labeling Project**
---
The Labeling Project folder contains multiple folder:
- **results**:
    Here the results of the labeling process are stored.
- **test folder**:
    Here is a small set of frames and the corresponding saved.
- **avg_polygons**
    Here are files stored, which save average polygons created for each damage type

### **Tables**
---
Here are multiple tables stored, which serve as a backup and list to analyze and sort which damages should be labeled next.