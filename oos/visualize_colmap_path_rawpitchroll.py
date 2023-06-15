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

def get_image_quaternions(recording_id):
    export_folder = os.path.join(exports_folder,recording_id)
    colmap_path = os.path.join(export_folder, "colmap_EM_export")
    cameras, images, points = read_write_model.read_model(colmap_path, ".txt")
    quaternions = []
    #sort iamge ids by image name
    image_ids = sorted(images.keys(), key=lambda x: images[x].name)
    for image_id in image_ids:
        image = images[image_id]
        quaternions.append(image.qvec)
    return quaternions
def get_yaw_pitch_roll_from_one_quaternion(q):
    yaw = np.arctan2(2*(q[0]*q[1] + q[2]*q[3]), 1 - 2*(q[1]**2 + q[2]**2))
    pitch = np.arcsin(2*(q[0]*q[2] - q[3]*q[1]))
    roll = np.arctan2(2*(q[0]*q[3] + q[1]*q[2]), 1 - 2*(q[2]**2 + q[3]**2))
    return np.array([yaw, pitch, roll])

#return numpy array of shape (n,3) where n is the number of images
def get_yaw_pitch_roll_from_quaternion(qs):
    yaw_pitch_roll = np.zeros((len(qs),3))
    for i,q in enumerate(qs):
        yaw_pitch_roll[i] = get_yaw_pitch_roll_from_one_quaternion(q)
    return yaw_pitch_roll


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

def plot_one_yaw_pitch_roll():
    recording_ids = os.listdir(exports_folder)
    recording_ids = os.listdir(exports_folder)
    #if the recording does not have colmap_EM_export/cameras.txt remove it from the list
    recording_ids = [recording_id for recording_id in recording_ids if os.path.exists(os.path.join(exports_folder, recording_id, "colmap_EM_export", "cameras.txt"))]
    random.shuffle(recording_ids)
    yaw_pitch_roll = get_yaw_pitch_roll_from_quaternion(get_image_quaternions(recording_ids[0]))
    #create a figure with 3 subplots in polar coordinates
    fig, ax = plt.subplots(3,1, subplot_kw=dict(projection='polar'))
    #add a title
    plt.title(recording_ids[0][:16])
    #change figure size
    fig.set_size_inches(5, 15)
    for i in range(3):
        ax[i].scatter(yaw_pitch_roll[:,i], np.arange(len(yaw_pitch_roll)))
        ax[i].set_theta_zero_location("N")
        #add a title
        ax[i].set_title(["Yaw", "Pitch", "Roll"][i])
        ax[i].set_yticklabels([])

    
    #put space between the subplots
    plt.subplots_adjust(hspace=0.5)
    



    plt.savefig("plots/yaw_pitch_roll{}.png".format(recording_ids[0]))

plot_one_yaw_pitch_roll()
#plot_one_path()
#plot_a_few_paths()
