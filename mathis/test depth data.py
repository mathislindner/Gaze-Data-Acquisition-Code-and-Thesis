import numpy as np
import os
from constants import *
from matplotlib import pyplot as plt
import cv2

recording_id = "test"
recording_folder = os.path.join(recordings_folder, str(recording_id))
depth_array = np.load(os.path.join(recording_folder, "depth_array.npz"))
rgb_pngs = os.listdir(os.path.join(recording_folder, "rgb_pngs"))
#plot all the depth images to scoll through them

#plot the 100th rgb image
"""rgb_image = cv2.imread(os.path.join(recording_folder, "rgb_pngs", rgb_pngs[100]))
plt.imshow(rgb_image)
plt.show()"""

#plot the 100th depth image
depth_image = depth_array["arr_0"][150]
max_depth = np.max(depth_image)
min_depth = np.min(depth_image)
range = max_depth - min_depth
depth_instensity = depth_image
plt.imshow(depth_instensity)
plt.show()

#print depth at pixel 334, 218
#print(depth_array["arr_0"][100][20, 225])