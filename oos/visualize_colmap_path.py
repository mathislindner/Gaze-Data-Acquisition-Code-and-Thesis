import sys
sys.path.append("/scratch_net/snapo/mlindner/docs/gaze_data_acquisition")
from dependencies.constants import  *
from dependencies.colmap_helpers import read_write_model
import os
import matplotlib.pyplot as plt
import numpy as np
import random

def get_image_positions(recording_id):
    export_folder = os.path.join(exports_folder,recording_id)
    colmap_path = os.path.join(export_folder, "colmap_EM_export")
    cameras, images, points = read_write_model.read_model(colmap_path, ".txt")
    translation_vectors = []
    #sort iamge ids by image name
    image_ids = sorted(images.keys(), key=lambda x: images[x].name)
    for image_id in image_ids:
        image = images[image_id]
        translation_vectors.append(image.tvec)
    return translation_vectors

def get_2d_image_positions(recording_id):
    translation_vectors = get_image_positions(recording_id)
    xyz = np.array(translation_vectors)
    xy = xyz[:,0:2]
    #connect the points
    xy = np.vstack((xy, xy[0]))
    return xy

def plot_one_path():
    recording_ids = os.listdir(exports_folder)
    #if the recording does not have colmap_EM_export/cameras.txt remove it from the list
    recording_ids = [recording_id for recording_id in recording_ids if os.path.exists(os.path.join(exports_folder, recording_id, "colmap_EM_export", "cameras.txt"))]
    random.shuffle(recording_ids)
    xy = get_2d_image_positions(recording_ids[0])
    plt.plot(xy[:,0], xy[:,1])
    #add a title
    plt.title(recording_ids[0])
    plt.show()


def plot_a_few_paths():
    recording_ids = os.listdir(exports_folder)
    #if the recording does not have colmap_EM_export/cameras.txt remove it from the list
    recording_ids = [recording_id for recording_id in recording_ids if os.path.exists(os.path.join(exports_folder, recording_id, "colmap_EM_export", "cameras.txt"))]
    list_of_xy = []
    random.shuffle(recording_ids)
    for recording_id in recording_ids[:9]:
        xy = get_2d_image_positions(recording_id)
        list_of_xy.append(xy)
    fig, ax = plt.subplots(3,3)
    for i,xy in enumerate(list_of_xy):
        ax[i//3,i%3].scatter(xy[:,0], xy[:,1], s=1)
        #connect the points
        ax[i//3,i%3].plot(xy[:,0], xy[:,1])
        #add a title
        ax[i//3,i%3].set_title(recording_ids[i])
    plt.show()

plot_one_path()
#plot_a_few_paths()
