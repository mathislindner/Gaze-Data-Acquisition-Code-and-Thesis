# Gaze Data Acquisition
## Introduction
This repository contains the code for the data acquisition of the gaze data. The data acquisition is done using the Pupil Labs glasses. The code is written in Python and bash and uses the Pupil Labs API for data acquisition. You can read the details in te pdf Thesis report pdf.
### The Structure of the Pipelines
#### Recording Pipeline
![The Structure of Recording Pipeline](/docs/images/Recording.png)
#### Post Processing Pipeline
![The Structure of Post Processing Pipeline](/docs/images/Post-Processing_Pipeline.png)
## Data-set Results
![Data-Set Examples](/docs/images/dataset_example.png)
## Installation
Use anaconda to install the environment_linux.yml according to your operating system. The environment file contains all the dependencies required for the code to run. The code is tested on Debian GNU/Linux 10 and Windows 10.
## Usage
1. To start the data acquisition, run the following command:
```python record.py```
2. The code will give you a prompt to explain how to use it:
    - ```---> Press right arrow to start recording```
    - ```---> Press left arrow to stop recording```
    - ```---> Press space to trigger an event```
    - ```---> Press del to cancel the recording```
    - ```---> Press esc to exit```
3. Once the recording is finished, wait for the recording to be uploaded to the pupil cloud and processed and the run
```python post_process.py```

## Protocol
The protocol for the data acquisition is as follows:
1. The participant is standing in front of the wall with the calibration pattern.
2. The participant is asked to look at the center of the pattern.
3. The laser pointer is turned on
4. The recording is started
5. The laser pointer will be pointed at each of the 5 points, one by one, and the participant is asked to look at the laser pointer for 3 seconds. The operator will ask for a confirmation from the participant before pressing space to trigger an event.
6. The participant is asked to move the next position and the repeat step 5.
7. The recording is stopped.