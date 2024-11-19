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

#### Sam2 repo

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

#### Install this repo

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

Before being able to just run the main.py, you'll need to set up the set path inside the config file.

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

### **Label with Folder Mode**

1. Prepare folders with Frames
2. Open those folders and label
3. Click on next to select next folder

### **Test Mode**

1. Just run and the Test folder opens

## User Interface

### Window

The Window opens when the Frames from the video are loaded.
On the Top there is the **menu bar**. In it there are Buttons to:

- add new observations
- reload and edit the grid
- reload sam2
- activate left click modes, like marking up frames, setting new splits and **deleting labels and splits**

Below it is the **top frame**. On the left are Buttons to select which observation to track and on the right buttons to go to the next video. Also there is the *Add new Split* Button, which activates the ability to set new splits. The tracking of objects will only be done inside splits.

Below that is the **second frame**. On the left are the visibilities of the different objects toggleable and on the right are buttons to extract further or other frames from the source video.

The **grid** is the main part of this window. Here You can click on the Images to open and label them. Be sure to have selected the right object before clicking on an image.

### Key Presses

#### Main Window

- Mousewheel and CTRL: Zoom and change Gridsize
- Rightclick: Activate Splitting Mode

#### Annotation Window

- Left Click: Positive Point
- Right Click: Negative Point
- Backspace: Remove last added Point

## Folder Structure

### **Code**

Here is the Code for the project stored. Refer to its readme for a better explanation.

### **Labeling Project**

The Labeling Project folder contains multiple folder:

- **results**:
    Here the results of the labeling process are stored.
- **test folder**:
    Here is a small set of frames and the corresponding json saved.
- **avg_polygons**
    Here are files stored, which save average polygons created for each damage type
- **coco_format**
    Here are the images and its json created, after running the convert to coco file

### **Infos and Tables**

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

- [Multiple libiomp5md files running:](https://www.programmersought.com/article/53286415201/)

- [C++ files missing](https://stackoverflow.com/questions/77666734/vs-code-error-could-not-find-c-program-files-x86-microsoft-visual-studio-ins)

- [Anaconda not in VSCode running](https://stackoverflow.com/questions/54828713/working-with-anaconda-in-visual-studio-code)

- [And all other Errors, please look at](https://github.com/facebookresearch/sam2/blob/main/INSTALL.md)
