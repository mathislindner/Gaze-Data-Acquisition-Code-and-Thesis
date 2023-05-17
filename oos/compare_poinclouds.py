from constants import *
import numpy as np
import pandas as pd
try:
    import open3d as o3d
except:
    pass
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

#TODO: instead of just using the 90th frame, average over a few frames from the beginning of the recording
def get_depth_distances_array(recording_path, image_id = 95):
    depth_camera_distances = np.load(os.path.join(recording_path, "depth_array.npz"))
    file_name = depth_camera_distances.files[0]
    return depth_camera_distances[file_name][95] #depth_camera_distances[file_name][95] is the depth array of the 90th frame

def get_pointcloud_o3d(points_3d, colors):
    pointcloud = o3d.geometry.PointCloud()
    pointcloud.points = o3d.utility.Vector3dVector(points_3d[:, :3])
    pointcloud.colors = o3d.utility.Vector3dVector(colors)
    return pointcloud

#pointclouds being a list of o3d pointclouds
def draw_pointclouds(pointclouds):
    o3d.visualization.draw_plotly(pointclouds)

#returns the colmap image dict
def get_colmap_depth_image(images):
    for image_id in images:
        if images[image_id].name == "depth_rgb.png":
            return images[image_id]
        
def get_colmap_depth_camera(images, cameras):
    colmap_depth_image = get_colmap_depth_image(images)
    return cameras[colmap_depth_image.camera_id]

#returns the depths of the points thatare non zero in from the depth array
def get_depths_and_colmap_point_ids(colmap_depth_image, colmap_points, depth_array):
    #get the visible points
    # TODO depth camera hardcoded intrinsics
    fx_d = fy_d = 388.0116271972656
    cx_d = 321.6023254394531
    cy_d = 241.12362670898438
    fx_rgb = 616.2463989257812
    fy_rgb = 616.6265258789062
    cx_rgb = 312.24853515625
    cy_rgb = 250.3607940673828

    visible_colmap_point_ids, depths, distances = [], [], []
    for point_ids, pixel_location in zip(colmap_depth_image.point3D_ids, colmap_depth_image.xys):
        if point_ids != -1:
            pixel_location = np.round(pixel_location).astype(int) #round pixel locations
            u = pixel_location[0]
            v = pixel_location[1]
            d = depth_array[v, u] / 1000.0 #convert to meters (because the pointcloud is in meters)
            if d != 0:
                xyz = np.array([(u-cx_d)/fx_d, (v-cy_d)/fy_d, 1.0])
                xyz *= d
                distances.append(np.linalg.norm(xyz))
                visible_colmap_point_ids.append(point_ids)
                depths.append(d)
                
    return np.array(depths), np.array(distances),  np.array(visible_colmap_point_ids)

def get_scale(colmap_cameras, colmap_images, colmap_points, depth_array):
    colmap_depth_image = get_colmap_depth_image(colmap_images)
    depths, distances_d, point_ids = get_depths_and_colmap_point_ids(colmap_depth_image, colmap_points, depth_array)
    visible_3Dpoints_by_depth_camera = np.array([colmap_points[point_id].xyz for point_id in point_ids])
    # COLMAP gives world_to_camera pose, 
    # which means that camera position in world coordinates is -R_w_2_c.T @ t_w_2_c
    # https://colmap.github.io/format.html#images-txt
    #camera_position = colmap_depth_image.tvec # OLD
    camera_position = -read_write_model.qvec2rotmat(colmap_depth_image.qvec).T @ colmap_depth_image.tvec
    #calculate distance between camera and points
    distances_colmap = np.linalg.norm(visible_3Dpoints_by_depth_camera - camera_position[None,...], axis=1)
    #calculate scale
    scale = np.mean(distances_d / distances_colmap)
    return scale 
############################################################################################################
sparse_cameras, sparse_images, sparse_points = get_colmap_sparse_model(recording_path)
dense_cameras, dense_images, dense_points = get_colmap_dense_model(recording_path)
depth_distances_array = get_depth_distances_array(recording_path)


sparse_scale = get_scale(sparse_cameras, sparse_images, sparse_points, depth_distances_array)
dense_scale = get_scale(dense_cameras, dense_images, dense_points, depth_distances_array)

print("sparse scale: ", sparse_scale)
print("dense scale: ", dense_scale)
############################################################################################################

#input are numpy arrays of shape pointcloud: (n, 3), R: (3, 3), t: (3), scale: float
def transform_pointcloud(pointcloud, R, t, scale):
    #t = -t.T @ R
    #transformation_matrix = np.eye(4)
    #scaling_matrix = np.eye(4)*scale
    #transformation_matrix[:3, :3] = R
    #transformation_matrix[:3, 3] = t 
    #transformation_matrix[3, 3] = 1
    #transformation_matrix = scaling_matrix @ transformation_matrix
    #pointcloud = np.vstack((pointcloud.T, np.ones(pointcloud.shape[0])))
    #pointcloud = transformation_matrix.T @ pointcloud 
    #pointcloud = pointcloud[:3,:].T

    # apply all three transformations seperately to debug
    pointcloud = np.matmul(R, pointcloud.T).T
    pointcloud = np.add(pointcloud, t)
    pointcloud = pointcloud * scale

    #mirror on x,y plane
    #
    
    return pointcloud

#from colmap to depth camera
def get_rotation_and_translation_matrix(colmap_cameras, colmap_images):
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

#returns the transformed colmap pointcloud and colors as o3d pointcloud
def get_transformed_colmap_as_o3d(colmap_cameras, colmap_images, colmap_points, scale):
    colmap_point_ids = list(colmap_points.keys())
    colmap_xyz = np.array([colmap_points[point_id].xyz for point_id in colmap_point_ids])
    colmap_rgb_colors = np.array([colmap_points[point_id].rgb for point_id in colmap_point_ids])
    rotation, translation = get_rotation_and_translation_matrix(colmap_cameras, colmap_images)
    transformed_colmap_points = transform_pointcloud(colmap_xyz, rotation, translation, scale)

    #colmap_camera_point_xyz = get_colmap_depth_image(colmap_images).tvec
    #colmap_camera_point_transformed = transform_pointcloud(colmap_camera_point_xyz, rotation, translation, scale)

    o3d_pointcloud = o3d.geometry.PointCloud()
    o3d_pointcloud.points = o3d.utility.Vector3dVector(transformed_colmap_points)
    o3d_pointcloud.colors = o3d.utility.Vector3dVector(colmap_rgb_colors)
    return o3d_pointcloud

#returns the transformed colmap pointcloud and colors as o3d pointcloud
def get_transformed_colmap_ply_as_o3d(colmap_cameras, colmap_images, colmap_points, scale):
    #colmap_point_ids = list(colmap_points.keys())
    colmap_fused_ply = o3d.io.read_point_cloud(os.path.join(recording_path, 'colmap_ws', 'automatic_recontructor','dense','0',"fused.ply"))
    colmap_xyz = np.asarray(colmap_fused_ply.points)
    colmap_rgb_colors = np.asarray(colmap_fused_ply.colors)

    #colmap_xyz = np.array([colmap_points[point_id].xyz for point_id in colmap_point_ids])
    #colmap_rgb_colors = np.array([colmap_points[point_id].rgb for point_id in colmap_point_ids])
    rotation, translation = get_rotation_and_translation_matrix(colmap_cameras, colmap_images)
    transformed_colmap_points = transform_pointcloud(colmap_xyz, rotation, translation, scale)

    #colmap_camera_point_xyz = get_colmap_depth_image(colmap_images).tvec
    #colmap_camera_point_transformed = transform_pointcloud(colmap_camera_point_xyz, rotation, translation, scale)

    o3d_pointcloud = o3d.geometry.PointCloud()
    o3d_pointcloud.points = o3d.utility.Vector3dVector(transformed_colmap_points)
    o3d_pointcloud.colors = o3d.utility.Vector3dVector(colmap_rgb_colors)
    return o3d_pointcloud

def get_depth_camera_pointcloud_as_o3d(recording_path, nr_points=50000):
    path = os.path.join(recording_path,"meshed_depth_camera.ply")
    mesh = o3d.io.read_triangle_mesh(path)
    pointcloud  = mesh.sample_points_uniformly(number_of_points=nr_points)

    M = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
    pointcloud_np = np.matmul(M, np.asarray(pointcloud.points).T).T
    R_rgb_2_d = np.array([[ 0.999967098236084,  0.006591256242245436, 0.0047245752066373825], 
                          [-0.006585866678506136,  0.9999776482582092,  -0.0011554613010957837], 
                          [-0.004732085391879082,  0.001124307862482965, 0.9999881982803345]])
    t_rgb_2_d = np.asarray([[-0.014696360565721989],
                            [-7.160441600717604e-05],
                            [-0.0003331863263156265]])
    pointcloud_np = (np.matmul(R_rgb_2_d, pointcloud_np.T) + t_rgb_2_d).T
    pointcloud.points = o3d.utility.Vector3dVector(pointcloud_np)

    return pointcloud

depth_pointcloud = get_depth_camera_pointcloud_as_o3d(recording_path)
sparse_camera_pointcloud = get_transformed_colmap_as_o3d(sparse_cameras, sparse_images, sparse_points, sparse_scale)
dense_camera_pointcloud = get_transformed_colmap_as_o3d(dense_cameras, dense_images, dense_points, dense_scale)
dense_camera_ply_pointcloud = get_transformed_colmap_ply_as_o3d(dense_cameras, dense_images, dense_points, dense_scale).voxel_down_sample(voxel_size=0.005)

pointcloud_xyz_tmp = np.asarray(dense_camera_ply_pointcloud.points)
pointcloud_rgb_tmp = np.asarray(dense_camera_ply_pointcloud.colors)
h_d, w_d = depth_distances_array.shape[0],  depth_distances_array.shape[1]
colmap_proj_d_tmp = np.zeros((h_d, w_d, 3))
colmap_proj_d_count_tmp = np.zeros((h_d, w_d, 1))
fx_d_rgb = 616.2463989257812
fy_d_rgb = 616.6265258789062
cx_d_rgb = 312.24853515625
cy_d_rgb = 250.3607940673828
pointcloud_uv_tmp = pointcloud_xyz_tmp[:, :2] / pointcloud_xyz_tmp[:, 2:] 
pointcloud_uv_tmp[:, 0] = pointcloud_uv_tmp[:, 0] * fx_d_rgb + cx_d_rgb
pointcloud_uv_tmp[:, 1] = pointcloud_uv_tmp[:, 1] * fy_d_rgb + cy_d_rgb
pointcloud_uv_tmp = np.rint(pointcloud_uv_tmp).astype(np.int32)
mask_tmp = (pointcloud_uv_tmp[:, 0] >= 0)*(pointcloud_uv_tmp[:, 0] < w_d)*(pointcloud_uv_tmp[:, 1] >= 0)*(pointcloud_uv_tmp[:, 1] < h_d)
pointcloud_uv_tmp = pointcloud_uv_tmp[mask_tmp]
pointcloud_rgb_tmp = pointcloud_rgb_tmp[mask_tmp]

for i, (u, v) in enumerate(pointcloud_uv_tmp):
    colmap_proj_d_tmp[v, u, :] = pointcloud_rgb_tmp[i, :]
    colmap_proj_d_count_tmp[v, u, 0] += 1.0
colmap_proj_d_count_tmp[colmap_proj_d_count_tmp == 0] = 1.0
colmap_proj_d_tmp /= colmap_proj_d_count_tmp

import matplotlib.pyplot as plt
plt.imshow(colmap_proj_d_tmp)
plt.savefig('colmap_proj_2_dcam_matplotlib.png')
plt.close()
import matplotlib.image
matplotlib.image.imsave('colmap_proj_2_dcam.png', colmap_proj_d_tmp)

#o3d.visualization.draw_plotly([depth_pointcloud, dense_camera_pointcloud],  width=1920, height=1080)
o3d.visualization.draw_plotly([depth_pointcloud, sparse_camera_pointcloud],  width=1920, height=1080)
#o3d.visualization.draw_plotly([depth_pointcloud, dense_camera_ply_pointcloud],  width=1920, height=1080)
#o3d.visualization.draw_plotly([depth_pointcloud],  width=1920, height=1080)