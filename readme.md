# SAM2 Interactive Object Labeling Project

This project provides a streamlined, interactive interface for object labeling using SAM2. The process begins with converting a video into individual frames, which are then processed and labeled and finally saved in a json.

## Requirements
- Windows or Linux (Only tested on Windows so far but Linux should also work)
- A modern Cuda and cuDNN capable Nvidia GPU is needed
- Enough Storage for SAM2 and Nvidia Drivers

## Installation
It is recommended to install everything inside a conda environment. In this conda environment we will install everything which is needed to run SAM2 and after that install the necessary Nvidia Drivers.
At the end we will set up the Paths the Code and then its ready to run!

### Code Editor
If you dont already have an editor for Code, you can download VSCode via this Terminal Command:
``` bash
winget install vscode
```

---
### Python, Git and Anaconda Installation
You will need Python 3.12.4 and Git. More modern versions of Python might work, but are untested!

To install open your Terminal and run:
#### Python
``` bash
winget install --id=Python.Python.3.12 -v "3.12.4" -e
```

#### Git

``` bash
winget install -e --id Git.Git
```

#### Anaconda
``` bash
winget install -e --id Anaconda.Anaconda3
```
---

### Setting up Anaconda

#### Creating a Conda Environment
For creating a new Anaconda Environment, open the freshly installed ``anaconda prompt`` terminal.
You can create a new Conda Environment, for example named ``sam2``, with following command: 
``` bash
conda create -n sam2 python
```
You can now enable your environment with:
``` bash
conda activate sam2
```
#### Preparing Powershell
We will need to set up Powershell, so that it automatically opens conda for us.
Open Powershell as an Admin and run following Command:

``` powershell
Set-ExecutionPolicy RemoteSigned
```
Now we can switch back to the ``anaconda prompt`` terminal and input:
``` bash
conda init PowerShell
```
Close all Terminal Windows now. If you reopen the normal terminal, conda will be activated automatically.

---
### Nvidia Drivers
First take a look, what the most recent CUDA Version PyTorch supports is, then first install the Nvidia Drivers.

You can check PyTorch from their [official Website](https://pytorch.org/).
Scroll down a bit and it will give you option, on what pytorch version you want to download.
Select:
1. **Stable**
2. Your Os, so **Windows** or **Linux**
3. **Conda** as the Package
4. **Python** as its Language
5. For the Compute Platform use the highest version of **Cuda**, as of October.2024 this is **Cuda 12.4**


Now you will get a command, which will install pytorch, and all of its dependencies. 
**Dont Run the Command you get yet!** 

First we have to Install the Cuda and cuDNN Drivers. For example i will need to install Cuda 12.4. You can access the archive with all **Cuda Toolkit** versions [here](https://developer.nvidia.com/cuda-toolkit-archive).

When you have found your Cuda Version, just select your Operating System, your Architecture, the Version of your OS and the type of installer you want and download the installer. 
After the download is finished, run it and check the box to add the path to your PATH environment variable.

Now you need the **cuDNN Library**, you can download it [here](https://developer.nvidia.com/cudnn)

**Add CUDA_HOME as an environment variable:**
After you have installed Cuda, you have to add it to your System Environment Variable. Just type in Evironment Variable into your windows Menu and add as a new Global Path:
1. Name: **CUDA_HOME**
2. Value: <Path/to/your/Cuda/Folder>, e.g. C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4

### C++ Libraries
We will need C++ Libraries for PyTorch, For that we have to download Microsoft Visual Studio. **This is not the Code Editor Visual Studio Code, VSCode!** 
Download the Installer from Microsofts Website [here](https://visualstudio.microsoft.com/de/visual-cpp-build-tools/).

Just open the Installer and select the ``C++ Developer Tools`` option when the Package Selection opens. Now you can download and install.

### Python Libraries
Open your terminal and activate your conda environment.
We need to install 2 libraries, to ensure the rest opf the operations follow smoothly:
``` python
conda install conda-forge::setuptools
```
and:
``` python
conda install conda-forge::matplotlib
```


### PyTorch
After everything else has been installed, now we can install PyTorch [from their Website.](https://pytorch.org/).
Select everything as you have done before and input your command into your activated conda environment.

The Command may look something like this:

``` bash
conda install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia
```


---
### Repositories
You will need the repository of [SAM2](https://github.com/facebookresearch/sam2) and this repository.
First we have to install SAM2s repo.

#### Sam2 repo:
Open your Terminal in your desired installation directory and make sure to switch to your created conda environment.

First download the repo:
``` bash
git clone https://github.com/facebookresearch/sam2.git
```

after the download is finished, cd into it with:

``` bash
cd sam2
```

and install the requirements with:

``` bash
pip install -e .
```
and
``` bash
pip install -e ".[notebooks]"
```

#### Install this repo:
Go back to your installation directory and run:
``` bash
git clone https://github.com/kyzira/SAM2-Interactive-Object-Labeling-Project.git
```

after the download is finished, cd into it with:

``` bash
cd SAM2-Interactive-Object-Labeling-Project
```

and install all needed libraries with

``` bash
pip install -r requirements.txt
```


## Getting Started
Before being able to just run the main.py, you'll need to set up the set path inside the code.

### Download Checkpoints
First you will need the Checkpoints provided by SAM2. You can find their download links on their [Github Repo](https://github.com/facebookresearch/sam2) under the section `Download Checkpoints`.
Download your preferred Model, i would recommend eiter the large or the tiny model. After downloading, save the checkpoint in your sam2 directory under ``checkpoints``.

### Cofiguration and Set Up Labeling Tool
Open the config.yaml file in the root Folder of this repo, here you can edit the Settings. 

#### Modes
first take a look at which mode you want to use (List Mode, Test Mode, View Mode, Auto Mode). 
- List Mode: follows a csv file and opens the next line after finishing labeling the current line. If in the Table a column named `Label` is present, that entry will be automatically entered as a label.
- Test Mode: This openes a saved example within this repo, to test and demonstrate features.
- Folder Mode: This lets you open any folder with cut open frames in it. You can label from there or if there is already a json file with masks one folder above, they will be drawn and editable. 
- Auto Mode: This allows the integration of a YOLOv8 Model to automatically label a whole video. WORK IN PROGRESS!

#### SAM2 Model Paths
Here you have to put in the absolute path to your SAM2 Checkpoint which you have downloaded earlier, and the path to its corresponding config file.
The config file is located inside the sam2 repo folder under ``sam2/sam2/configs/sam2.1/``.

#### List Mode Paths
Here you can input the path to your input table and the folder, in which a results folder is created where all the cut frames and their masks as a json file is stored.

#### Table Columns
This is a list of all columns of your csv table, which you want to save as an Info part inside your Json. This will be the first entry with the key "info".

#### Object Add Buttons
Every entry of this list is used to create a seperate button to click in the app to add new Objects fast.

#### Test Mode Paths
These Paths are local paths to the main.py 's path with example frames.

#### Test Mode Table
This is just a table with example values to demonstrate how a result might look in a json file.

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


## Known Errors

Try the following Steps if Anything breaks or does not work as inteded:

- Downgrade Python to 3.12.4
    
    If the Python Version is too new, there might come up a lot of issues.
    Check your installed version with

    ``` python
    python --version
    ```

    and install an other Version like:

    ``` python
    conda install python=3.12.4
    ```

- Multiple libiomp5md files running:
    
    https://www.programmersought.com/article/53286415201/

- C++ files missing
    
    https://stackoverflow.com/questions/77666734/vs-code-error-could-not-find-c-program-files-x86-microsoft-visual-studio-ins

- Anaconda not in VSCode running

    https://stackoverflow.com/questions/54828713/working-with-anaconda-in-visual-studio-code
    
- And all other Errors, please look at:

    https://github.com/facebookresearch/sam2/blob/main/INSTALL.md
    