from constants import *
import numpy as np
import pandas as pd
import open3d as o3d
from colmap_testing.colmap_helpers import read_write_model
import os

recording_id = "ff0acdab-123d-41d8-bfd6-b641f99fc8eb"
recording_path = os.path.join(recordings_folder, recording_id)

def get_colmap_sparse_model(recording_path):
    path = os.path.join(recording_path, "colmap_ws/colmap_out_1/sparse")
    cameras, images, points_3d = read_write_model.read_model(path, ".bin")
    return cameras, images, points_3d

def get_colmap_dense_model(recording_path):
    path = os.path.join(recording_path, "colmap_ws/automatic_recontructor/dense/0/sparse")
    cameras, images, points_3d = read_write_model.read_model(path, ".bin")
    return cameras, images, points_3d

def get_depth_camera_pointcloud(recording_path, nr_points=20000):
    path = os.path.join(recording_path,"meshed_depth_camera.ply")
    mesh = o3d.io.read_triangle_mesh(path)
    pointcloud  = mesh.sample_points_uniformly(number_of_points=nr_points)
    return pointcloud

#transform pointcloud to different coordinate system
#pointcloud being a 3d numpy array
def transform_pointcloud_numpy(pointcloud, R, t):
    pointcloud = np.matmul(R, pointcloud.T).T
    pointcloud = pointcloud + t
    return pointcloud

def get_pointcloud_o3d(points_3d, colors):
    pointcloud = o3d.geometry.PointCloud()
    pointcloud.points = o3d.utility.Vector3dVector(points_3d[:, :3])
    pointcloud.colors = o3d.utility.Vector3dVector(colors)
    return pointcloud

#pointclouds being a list of o3d pointclouds
def draw_pointclouds(pointclouds):
    o3d.visualization.draw_plotly(pointclouds)

#returns the colmap image dict
def get_depth_image(images):
    depth_image_id = None
    for image_id in images:
        if images[image_id].name == "depth_rgb.png":
            depth_image_id = image_id
            break
    return images[image_id]

#returns the depths of the points thatare non zero in from the depth array
def get_depths_of_nonzero(depth_array, images, indices_of_nonzero):
    pixel_location_of_visible_points_by_depth_camera = depth_array.xys[indices_of_nonzero]
    #round pixel locations
    pixel_location_of_visible_points_by_depth_camera = np.round(pixel_location_of_visible_points_by_depth_camera).astype(int)
    depths = []
    for pixel_location in pixel_location_of_visible_points_by_depth_camera:
        depths.append(depth_array.depths[pixel_location[1], pixel_location[0]])
    depths = np.array(depths)
    return depths

    

def get_scale(colmap_cameras, colmap_images, colmap_points, depth_camera_distances):
    depth_array = get_depth_image(colmap_images)
    indices_of_nonzero = [i for i in range (len(depth_array.point3D_ids)) if depth_array.point3D_ids[i] != -1]
    depths_of_nonzero = get_depths_of_nonzero(colmap_images, indices_of_nonzero)
    visible_colmap_points = colmap_points[indices_of_nonzero].xyz
    camera_position = get_depth_image(colmap_images).tvec

    #calculate distance between camera and points
    distances = np.linalg.norm(visible_colmap_points - camera_position, axis=1)
    #calculate scale
    scale = np.mean(depths_of_nonzero / distances)
    return scale

