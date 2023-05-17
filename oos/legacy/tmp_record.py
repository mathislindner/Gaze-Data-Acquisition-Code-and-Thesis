
import os
import time

import numpy as np

import cv2

from pynput import keyboard

from multiprocessing import Process, Event, Value

from uvc_stream import UVC_Source, DEV_SETTINGS

from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback
import logging


# # Define the codec and create VideoWriter object
# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter(os.path.join(SAVE_DIR, 'video.avi'), fourcc, 1.0, (400,  400))
# hf = h5py.File(os.path.join(SAVE_DIR, 'frames.h5'), 'w')
# hf.create_dataset(name='frames', data=None, shape=(1000, 400, 400), dtype=np.float32) #, maxshape=(0, 400, 400,)

# Too slow
# cv2.imwrite(os.path.join(SAVE_DIR, 'tmp.png'), frame.bgr)

# from turbojpeg import TurboJPEG
# jpeg = TurboJPEG()
# jpeg.decode(frame.jpeg_buffer)

# with open(os.path.join(SAVE_DIR, 'tmp_turbo.jpg'), "wb") as f:
#     f.write(frame.jpeg_buffer)

#out.write(frame.bgr)

#hf["frames"].resize((hf["frames"].shape[0] + 1), axis = 0)


class AcquisitionLogic:
    def __init__(self) -> None:
        self.recording_event = Event()
        self.storing_event = Event()
        self.event_i = Value('i', 0)
        self.t_record = 2.0
        self.t_store = self.t_record * 2.0

        self.action_key = keyboard.Key.up
        

    def on_press(self, key):
        # Skip. Recording is already activated.
        if self.recording_event.is_set():
            if key is self.action_key:
                print('Wait! Recording is currently activated.')
            return
        
        # Skip. Data storing is already activated.
        if self.storing_event.is_set():
            if key is self.action_key:
                print('Wait! Data storing is currently activated.')
            return
        
        # Skip. Wrong key.
        if key is not self.action_key:
            return
        
        # Start the recording event.
        self.recording_event.set()
        print(f'Started recording event. ({self.t_record} s)')

        # except AttributeError:
        #     print('special key {0} pressed'.format(
        #         key))
    
    def run_acquisition_logic(self):
        while True:

            # Wait for the recording event to start.
            self.recording_event.wait()
            assert not self.storing_event.is_set()
            # Wait for specified amount of time.
            time.sleep(self.t_record)
            # End the recording event
            self.recording_event.clear()
            print(f'Ended recording event.')

            # Start the storing event.
            self.storing_event.set()
            print(f'Started storing event. ({self.t_store} s)')
            # Wait for specified amount of time.
            time.sleep(self.t_store)
            # End the storing event
            self.storing_event.clear()
            print('Ended storing event.')

            self.event_i.value += 1


class StreamAcquisition:
    def __init__(self, source_cls, source_args, acquisition_logic, save_dir) -> None:
        self.source_cls = source_cls
        self.source_args = source_args
        self.recording_event = acquisition_logic.recording_event
        self.event_i = acquisition_logic.event_i
        self.save_dir = save_dir

        self.label = source_args['label']

    def stream_acquisition(self):
        # Start the source stream
        self.source = self.source_cls(**self.source_args)

        while True:
            # The loop iteration should not be entered during an active recording event
            assert not self.recording_event.is_set()

            frames = []
            timestamps = []
            # Wait for the button to be activated.
            # Then collect frames as long as the event remains True.
            self.recording_event.wait()
            print(self.source.uvc_capture)
            t_start = time.time()
            while self.recording_event.is_set():
                sample = self.source.recent_sample()
                #print(sample)
                if sample:
                    frame_i, t_i, _ = sample
                    frames.append(frame_i)
                    timestamps.append(t_i)
            self.print(f'Collected {len(frames)} frames. ({(time.time()-t_start):.4f} s)') 

            # Save all collected frames
            t_start = time.time()
            f_prefix = f'{self.event_i.value}_{self.label}'
            frames = np.asarray(frames)
            timestamps = np.asarray(timestamps)
            assert frames.shape[0] == timestamps.shape[0]
            np.save(os.path.join(self.save_dir, f'{f_prefix}_frames.npy'), frames)
            np.save(os.path.join(self.save_dir, f'{f_prefix}_timestamps.npy'), timestamps)
            self.print(f'Stored {frames.shape[0]} frames. ({(time.time()-t_start):.4f} s)') 
    
    def print(self, msg):
        print(f'[{self.label}] {msg}')

if __name__ == "__main__":

    install_rich_traceback()
    logging.basicConfig(
        level=logging.NOTSET,
        handlers=[RichHandler(level="DEBUG")],
        format="%(message)s",
        datefmt="[%X]",
    )


    SAVE_DIR = '/srv/beegfs02/scratch/aegis_cvl/data/data_collection/tmp/0_user/0_laser'

    acquisition_logic = AcquisitionLogic()


    # # Collect events until released
    # with keyboard.Listener(on_press=on_press) as listener:
    #     listener.join(event)
    # ...or, in a non-blocking fashion:
    listener = keyboard.Listener(on_press=acquisition_logic.on_press)
    listener.start()
    

    # Create a process for every sensor source
    which_device = 'pupil_invisible'
    cameras = ['eye_left'] #'eye_left', 'eye_right', 'world'
    processes = []
    for camera in cameras:
        dev_settings = DEV_SETTINGS[which_device][camera]
        arg_dict = {
            'frame_size': dev_settings['frame_size'],
            'frame_rate': dev_settings['fps'],
            'name': dev_settings['name'], #pc onlz sees the name as 'unknown'
            #'uid': dev_settings['uid'], #manually set in DEV_SETTINGS by looking at the output of uvc.get_device_list()
            'label': dev_settings['label'],
            'exposure_mode': 'auto'
        }
        #add assertion if the camera is not found
        #stream_acquisition = 
        processes.append(Process(target=StreamAcquisition(UVC_Source, arg_dict, acquisition_logic, SAVE_DIR).stream_acquisition))
    # start all processes
    for process in processes:
        process.start()

    acquisition_logic.run_acquisition_logic()

    # wait for all child processes to terminate
    for process in processes:
        process.join()


