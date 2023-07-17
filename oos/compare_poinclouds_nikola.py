import sys
sys.path.insert(1, '/home/nipopovic/Code/gaze_data_acquisition')
sys.path.insert(1, '/scratch_net/snapo/mlindner/docs/gaze_data_acquisition')
from dependencies.constants import *

import numpy as np
try:
    import open3d as o3d
except:
    pass
from dependencies.colmap_helpers import read_write_model
import os

import pyrealsense2 as rs

recording_id = "ff0acdab-123d-41d8-bfd6-b641f99fc8eb"
#recording_id = "3c9b343b-c076-4c93-9098-fc693503e7ca"
recording_path = os.path.join(recordings_folder, recording_id)

def get_colmap_sparse_model(recording_path):
    # 'colmap_EM_ws/exhaustive_matcher_out/world_and_depth/sparse'
    # "colmap_ws/colmap_out_1/sparse"
    path = os.path.join(recording_path, "colmap_EM_ws/exhaustive_matcher_out/world_and_depth/sparse")
    if not os.path.isdir(path):
        path = os.path.join(recording_path, "colmap_ws/colmap_out_1/sparse")
        if not os.path.isdir(path):
            raise NotADirectoryError
        
    cameras, images, points_3d = read_write_model.read_model(path, ".bin")
    return cameras, images, points_3d


def get_colmap_dense_model(recording_path):
    path = os.path.join(recording_path, "colmap_EM_ws/exhaustive_matcher_out/world_and_depth/dense")
    if not os.path.isdir(path):
        path = os.path.join(recording_path, "colmap_ws/automatic_recontructor/dense/0/sparse")
        if not os.path.isdir(path):
            raise NotADirectoryError
        
    cameras, images, points_3d = read_write_model.read_model(path, ".bin")
    return cameras, images, points_3d


def plot_o3d_geometries(geometries_list, plotly=False):        
    if plotly:
        o3d.visualization.draw_plotly(geometries_list,  width=1920, height=1080)
    else:    
        vis = o3d.visualization.Visualizer()
        vis.create_window()

        for g in geometries_list:
            vis.add_geometry(g)

        vis.poll_events()
        vis.update_renderer()
        vis.run()
        vis.destroy_window()


def get_depth_cam_model(recording_path, select_frame):
    bag_file_path = os.path.join(recording_path, 'realsensed435.bag')

    pipeline = rs.pipeline()

    config = rs.config()
    config.enable_device_from_file(bag_file_path, repeat_playback=False)

    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()
    device_product_line = str(device.get_info(rs.camera_info.product_line))

    found_rgb = False
    for s in device.sensors:
        if s.get_info(rs.camera_info.name) == 'RGB Camera':
            found_rgb = True
            break
    if not found_rgb:
        print("ERROR...The demo requires Depth camera with Color sensor")
        exit(0)

    # Start streaming
    profile = pipeline.start(config)

    playback = profile.get_device().as_playback()
    playback.set_real_time(False)

    # Get stream profile and camera intrinsics
    profile = pipeline.get_active_profile()
    depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
    depth_intrinsics = depth_profile.get_intrinsics()
    color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
    color_intrinsics = color_profile.get_intrinsics()
    depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
    #color_profile.get_extrinsics_to(depth_profile)

    # Create an align object
    # rs.align allows us to perform alignment of depth frames to others frames
    # The "align_to" is the stream type to which we plan to align depth frames.
    # When we align depth to color, the depth frame will inherit the color frames intrinsics
    # since it gives a depth value for every color frames value
    align_to = rs.stream.color
    align = rs.align(align_to)

    i=-1
    while True:
        # Grab camera data
        # Wait for a coherent pair of frames: depth and color
        try:
            frames = pipeline.wait_for_frames()
            # Align the depth frame to color frame
            playback.pause() #added this because else the frames are not saved correctly: https://stackoverflow.com/questions/58482414/frame-didnt-arrived-within-5000-while-reading-bag-file-pyrealsense2
        except:
            return None
        
        i += 1
        if not i == select_frame:
            playback.resume()
            continue

        aligned_frames = align.process(frames)

        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        aligned_depth_frame = aligned_frames.get_depth_frame()
        aligned_color_frame = aligned_frames.get_color_frame()

        # # Grab new intrinsics (may be changed by alignment)
        # aligned_depth_intrinsics = rs.video_stream_profile(
        #     aligned_depth_frame.profile).get_intrinsics()

        if not color_frame or not depth_frame or not aligned_depth_frame or not aligned_color_frame:
            print(f'ERROR...Invalid frame: {select_frame}')
            return None
        

        print(f'\nFound frame number: i:{i} rgb:{color_frame.frame_number}, depth:{depth_frame.frame_number}')
        
        depth_image = np.asanyarray(depth_frame.get_data()) * depth_scale
        color_image = np.asanyarray(color_frame.get_data())
        aligned_depth_image = np.asanyarray(aligned_depth_frame.get_data()) * depth_scale
        aligned_color_image = np.asanyarray(aligned_color_frame.get_data())

        # Create grid of pixel center positions in the uv space
        intrinsics = color_intrinsics
        w, h = intrinsics.width, intrinsics.height
        u_linspace = np.linspace(0 + 0.5, w - 0.5, w)
        v_linspace = np.linspace(0 + 0.5, h - 0.5, h)
        u, v = np.meshgrid(u_linspace, v_linspace)
        x = (u - intrinsics.ppx) / intrinsics.fx
        y = (v - intrinsics.ppy) / intrinsics.fy
        # Add 3rd coordinate and reshape to vector
        xyz_3d = aligned_depth_image[..., None] * np.dstack((x, y, np.ones_like(u)))
        return aligned_color_image, aligned_depth_image, xyz_3d


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
    #scale = np.median(ratios)

    # pts_colmap_can = (R_d_colmap @ pts_colmap.T + t_d_colmap[:, None]).T
    # scale = np.mean(np.linalg.norm(pts_d_can, axis=-1) / np.linalg.norm(pts_colmap_can, axis=-1))

    return scale 


#input are numpy arrays of shape pointcloud: (n, 3), R: (3, 3), t: (3), scale: float
def transform_pointcloud(pointcloud, R, t, scale):
    # Be careful that to properly apply scale to align colmap to depth camera
    # the transformation should be from world_2_depth before applying the scale
    return (R @ pointcloud.T + t[:, None]).T * scale

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
def get_transformed_colmap_as_o3d(colmap_cameras, colmap_images, colmap_points, scale, downsample):
    colmap_point_ids = list(colmap_points.keys())
    colmap_xyz = np.array([colmap_points[point_id].xyz for point_id in colmap_point_ids])
    colmap_rgb_colors = np.array([colmap_points[point_id].rgb for point_id in colmap_point_ids])
    rotation, translation = get_rotation_and_translation_matrix(colmap_cameras, colmap_images)
    transformed_colmap_points = transform_pointcloud(colmap_xyz, rotation, translation, scale)

    #colmap_camera_point_xyz = get_colmap_depth_image(colmap_images).tvec
    #colmap_camera_point_transformed = transform_pointcloud(colmap_camera_point_xyz, rotation, translation, scale)

    o3d_pointcloud = o3d.geometry.PointCloud()
    o3d_pointcloud.points = o3d.utility.Vector3dVector(transformed_colmap_points[::downsample])
    o3d_pointcloud.colors = o3d.utility.Vector3dVector(colmap_rgb_colors[::downsample]/255.0)
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


remote_vis = False
downsample = 4

sparse_cameras, sparse_images, sparse_points = get_colmap_sparse_model(recording_path)
try:
    dense_cameras, dense_images, dense_points = get_colmap_dense_model(recording_path)
except:
    print('Dense model not available, using sparse instead')
    dense_cameras = sparse_cameras; dense_images = sparse_images; dense_points = sparse_points
color_d_i, depth_d_i, xyz_d_i = get_depth_cam_model(recording_path, select_frame=95)

xyz_d_i_1 = xyz_d_i[295:481, 0:393].reshape(-1, 3)
color_d_i_1 = color_d_i[295:481, 0:393].reshape(-1, 3)
xyz_d_i_2 = xyz_d_i[206:346, 505:].reshape(-1, 3)
color_d_i_2 = color_d_i[206:346, 505:].reshape(-1, 3)
# xyz_d_i_sel = xyz_d_i_1
# color_d_i_sel = color_d_i_1
xyz_d_i_sel = np.concatenate([xyz_d_i_1, xyz_d_i_2], axis=0)
color_d_i_sel = np.concatenate([color_d_i_1, color_d_i_2], axis=0)
# TODO For mathis: Comment out below 2 lines to see colors in the aprtial depth pointcloud
color_d_i_sel = np.zeros_like(xyz_d_i_sel)
color_d_i_sel[:, 1] = 255.0

sparse_scale = get_scale(sparse_images, sparse_points, xyz_d_i)
dense_scale = get_scale(dense_images, dense_points, xyz_d_i)

print("sparse scale: ", sparse_scale)
print("dense scale: ", dense_scale)

# Depth pointcloud
depth_pointcloud = o3d.geometry.PointCloud()
depth_pointcloud.points = o3d.utility.Vector3dVector(xyz_d_i.reshape((xyz_d_i.shape[0]*xyz_d_i.shape[1], 3))[::downsample])
depth_pointcloud.colors = o3d.utility.Vector3dVector(color_d_i.reshape((color_d_i.shape[0]*color_d_i.shape[1], 3))[::downsample]/255.0)
depth_pointcloud_sel = o3d.geometry.PointCloud()
depth_pointcloud_sel.points = o3d.utility.Vector3dVector(xyz_d_i_sel[::downsample])
depth_pointcloud_sel.colors = o3d.utility.Vector3dVector(color_d_i_sel[::downsample]/255.0)

colmap_sparse_pointcloud = get_transformed_colmap_as_o3d(sparse_cameras, sparse_images, sparse_points, sparse_scale, downsample=1)
colmap_dense_pointcloud = get_transformed_colmap_as_o3d(dense_cameras, dense_images, dense_points, dense_scale, downsample)
colmap_dense_ply_pointcloud = get_transformed_colmap_ply_as_o3d(dense_cameras, dense_images, dense_points, dense_scale).voxel_down_sample(voxel_size=0.001)



pointcloud_xyz_tmp = np.asarray(colmap_sparse_pointcloud.points)
pointcloud_rgb_tmp = np.asarray(colmap_sparse_pointcloud.colors)
h_d, w_d = xyz_d_i.shape[0],  xyz_d_i.shape[1]
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
    colmap_proj_d_tmp[v, u, :] += pointcloud_rgb_tmp[i, :]
    colmap_proj_d_count_tmp[v, u, 0] += 1.0
colmap_proj_d_count_tmp[colmap_proj_d_count_tmp == 0] = 1.0
colmap_proj_d_tmp /= colmap_proj_d_count_tmp
colmap_proj_d_tmp[np.linalg.norm(colmap_proj_d_tmp, axis=-1) == 0.0] = np.ones(3)

plot_o3d_geometries([colmap_sparse_pointcloud], plotly=remote_vis)
plot_o3d_geometries([depth_pointcloud], plotly=remote_vis)
plot_o3d_geometries([depth_pointcloud_sel], plotly=remote_vis)
plot_o3d_geometries([depth_pointcloud_sel, colmap_sparse_pointcloud], plotly=remote_vis) 
plot_o3d_geometries([depth_pointcloud, colmap_sparse_pointcloud], plotly=remote_vis)

import matplotlib.pyplot as plt
plt.figure()
plt.imshow(color_d_i)
plt.imshow(colmap_proj_d_tmp, alpha=0.8)
if remote_vis:
    plt.savefig('colmap_proj_2_dcam_matplotlib_overlay.png')
else:
    plt.show()
plt.close()

plt.figure()
plt.imshow(colmap_proj_d_tmp)
if remote_vis:
    plt.savefig('colmap_proj_2_dcam.png')
else:
    plt.show()
plt.close()

plt.figure()
plt.imshow(color_d_i)
if remote_vis:
    plt.savefig('depth_img.png')
else:
    plt.show()
plt.close()