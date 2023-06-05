import sys
sys.path.insert(1, '/home/nipopovic/Code/gaze_data_acquisition')
sys.path.insert(1, '/scratch_net/snapo/mlindner/docs/gaze_data_acquisition')
from dependencies.constants import *

import numpy as np
from dependencies.colmap_helpers import read_write_model
import os

def get_colmap_sparse_model(recording_id):
    recording_path = os.path.join(recordings_folder, recording_id)
    path = os.path.join(recording_path, "colmap_EM_export")
    cameras, images, points_3d = read_write_model.read_model(path, ".txt")
    return cameras, images, points_3d

#TODO: instead of just using the 90th frame, average over a few frames from the beginning of the recording
def get_depth_distances_array(recording_path, image_id = 95):
    depth_camera_distances = np.load(os.path.join(recording_path, "depth_array.npz"))
    file_name = depth_camera_distances.files[0]
    return depth_camera_distances[file_name][95] #depth_camera_distances[file_name][95] is the depth array of the 90th frame

#returns the colmap image dict
def get_colmap_depth_image(images):
    for image_id in images:
        if images[image_id].name == "depth_rgb.png":
            return images[image_id]
#creates an array of colmap images same size as idxs
def get_colmap_world_images(images, idxs):
    #if idxs is not None, return the corresponding image
    images_out = np.empty(idxs.shape[0], dtype = object)
    for idx in idxs:
        for image_id in images:
            if images[image_id].name == "{}.png".format(idx):
                images_out[idx] = images[image_id]
    assert len(images_out) == idxs.shape[0]
    return images_out
            
def get_colmap_depth_camera(images, cameras):
    colmap_depth_image = get_colmap_depth_image(images)
    return cameras[colmap_depth_image.camera_id]

def get_colmap_world_camera(images, cameras, idx):
    colmap_depth_camera_id = cameras[get_colmap_depth_image(images).camera_id]
    camera_ids = cameras.keys()
    #world camera has the id that is not the depth camera id
    world_camera = cameras[camera_ids != colmap_depth_camera_id]
    return world_camera

#colmap to depth camera
def get_scale(colmap_images, colmap_points, xyz_d_i):
    colmap_depth_image = get_colmap_depth_image(colmap_images)

    pts_colmap_id, pts_colmap, pts_d_can = [], [], []
    for p_id, pixel_location in zip(colmap_depth_image.point3D_ids, colmap_depth_image.xys):
        if p_id != -1:
            pixel_location = np.round(pixel_location).astype(int) #round pixel locations
            u = pixel_location[0]
            v = pixel_location[1]
            if xyz_d_i[v, u, 2] != 0:
                pts_colmap_id.append(p_id)
                pts_colmap.append(colmap_points[p_id].xyz)
                pts_d_can.append(xyz_d_i[v, u])
    
    pts_colmap = np.asarray(pts_colmap); pts_d_can = np.asarray(pts_d_can)

    # COLMAP gives world_to_camera pose, 
    # which means that camera position in world coordinates is -R_w_2_c.T @ t_w_2_c
    # https://colmap.github.io/format.html#images-txt
    R_d_colmap = read_write_model.qvec2rotmat(colmap_depth_image.qvec)
    t_d_colmap = colmap_depth_image.tvec
    camera_position = -R_d_colmap.T @ t_d_colmap

    ratios = np.linalg.norm(pts_d_can, axis=-1) / np.linalg.norm(pts_colmap - camera_position[None,...], axis=-1)
    scale = np.mean(ratios)
    return scale 


#input are numpy arrays of shape pointcloud: (n, 3), R: (3, 3), t: (3), scale: float
def transform_pointcloud_depth_to_colmap(pointcloud, Rotation_matrix, translation_vector, scale):
    colmap_to_depth_tranformation_matrix = np.eye(4)
    colmap_to_depth_tranformation_matrix[:3, :3] = Rotation_matrix
    colmap_to_depth_tranformation_matrix[:3, 3] = translation_vector
    colmap_to_depth_tranformation_matrix[:3, 3] *= scale
    colmap_to_depth_tranformation_matrix[3, 3] = 1
    depth_to_colmap_tranformation_matrix = np.linalg.inv(colmap_to_depth_tranformation_matrix)
    transformed_pointcloud = np.ones((pointcloud.shape[0], 4))
    transformed_pointcloud[:, :3] = pointcloud
    transformed_pointcloud = transformed_pointcloud @ depth_to_colmap_tranformation_matrix.T
    return transformed_pointcloud[:, :3]

#from colmap to depth camera
def get_depth_rotation_and_translation_matrix(colmap_images):
    colmap_depth_image = get_colmap_depth_image(colmap_images)
    q_vec = colmap_depth_image.qvec
    t_vec = colmap_depth_image.tvec
    
    camera_orientation = read_write_model.qvec2rotmat(q_vec)
    camera_position = t_vec

    #convert to depth camera coordinate system
    #FIXME invert rotation and translation
    rotation = camera_orientation
    translation = camera_position
    
    return rotation, translation


def get_scale(colmap_images, colmap_points, xyz_d_i):
    colmap_depth_image = get_colmap_depth_image(colmap_images)

    pts_colmap_id, pts_colmap, pts_d_can = [], [], []
    for p_id, pixel_location in zip(colmap_depth_image.point3D_ids, colmap_depth_image.xys):
        if p_id != -1:
            pixel_location = np.round(pixel_location).astype(int) #round pixel locations
            u = pixel_location[0]
            v = pixel_location[1]
            if xyz_d_i[v, u] != 0:
                pts_colmap_id.append(p_id)
                pts_colmap.append(colmap_points[p_id].xyz)
                pts_d_can.append(xyz_d_i[v, u])
    
    pts_colmap = np.asarray(pts_colmap); pts_d_can = np.asarray(pts_d_can)

    # COLMAP gives world_to_camera pose, 
    # which means that camera position in world coordinates is -R_w_2_c.T @ t_w_2_c
    # https://colmap.github.io/format.html#images-txt
    R_d_colmap = read_write_model.qvec2rotmat(colmap_depth_image.qvec)
    t_d_colmap = colmap_depth_image.tvec
    camera_position = -R_d_colmap.T @ t_d_colmap

    ratios = np.linalg.norm(pts_d_can, axis=-1) / np.linalg.norm(pts_colmap - camera_position[None,...], axis=-1)
    scale = np.mean(ratios)
    #scale = np.median(ratios)

    # pts_colmap_can = (R_d_colmap @ pts_colmap.T + t_d_colmap[:, None]).T
    # scale = np.mean(np.linalg.norm(pts_d_can, axis=-1) / np.linalg.norm(pts_colmap_can, axis=-1))

    return scale 

def convert_3D_coordinates_from_depth_to_pupil_world(points_in_depth, recording_id):
    sparse_cameras, sparse_images, sparse_points = get_colmap_sparse_model(recording_id)
    rotation_colmap_to_depth, translation_colmap_to_depth = get_depth_rotation_and_translation_matrix(sparse_images)
    scale_colmap_to_depth = get_scale(sparse_images, sparse_points, get_depth_distances_array(os.path.join(recordings_folder, recording_id)))
    points_in_colmap = transform_pointcloud_depth_to_colmap(points_in_depth, rotation_colmap_to_depth, translation_colmap_to_depth, scale_colmap_to_depth)
    return points_in_colmap

def project_3D_points_to_pupil_world(points, recording_id, world_camera_idx):
    sparse_cameras, sparse_images, sparse_points = get_colmap_sparse_model(recording_id)
    colmap_world_images = get_colmap_world_images(sparse_images, world_camera_idx) #lsit of images
    colmap_world_camera = get_colmap_world_camera(sparse_images, sparse_cameras, world_camera_idx) #camera object

    world_camera_dimensions = (colmap_world_camera.width, colmap_world_camera.height)
    fx,fy,cx,cy = colmap_world_camera.params #pinhole camera model
    world_camera_instrinsics_matrix = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
    #get from world images
    world_camera_extrinsics_array = 0
    array_projected_points = np.empty((len(points), 2))
    for i, (point, colmap_world_image) in enumerate(zip(points, colmap_world_images)):
        if np.isnan(point).any():
            array_projected_points[i] = np.array([np.nan, np.nan])
            continue
        if colmap_world_image is None:
            array_projected_points[i] = np.array([np.nan, np.nan])
            continue
        #if point in nan, skip, add nan to array_projected_points
        rotation_matrix = read_write_model.qvec2rotmat(colmap_world_image.qvec)
        translation_matrix = colmap_world_image.tvec
        world_camera_extrinsics = np.eye(4)
        world_camera_extrinsics[:3, :3] = rotation_matrix
        world_camera_extrinsics[:3, 3] = translation_matrix

        #project points
        points_3D = np.ones((point.shape[0], 4))
        points_3D[:, :3] = point
        points_3D = points_3D @ world_camera_extrinsics.T
        points_3D = points_3D[:, :3]
        points_2D = points_3D @ world_camera_instrinsics_matrix.T
        points_2D = points_2D[:, :2] / points_2D[:, 2:]
        points_2D = points_2D.astype(int)
        #array_projected_points[i] = points_2D
        #FIXME: temporary
        array_projected_points[i] = np.array([np.nan, np.nan])
    return array_projected_points

"""recording_folder = os.path.join(recordings_folder, "83ee44f0-c9a3-4aea-8237-8f55c0de4fd9")
full_df = pd.read_csv(os.path.join(recording_folder, "full_df.csv"))
world_camera_idx = full_df["world_idx"].to_numpy()
points = np.array([[0,0,0], [1,1,1]])
project_3D_points_to_pupil_world(points,"83ee44f0-c9a3-4aea-8237-8f55c0de4fd9",world_camera_idx)"""