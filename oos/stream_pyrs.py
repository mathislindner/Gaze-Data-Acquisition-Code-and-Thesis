#stream pyreal sense camera to window
import pyrealsense2 as rs
import cv2
import numpy as np

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
profile = pipeline.start(config)
color_sensor = profile.get_device().query_sensors()[1]
j = 0
try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())
        if j % 10 == 9:
            #turn off auto exposure
            color_sensor.set_option(rs.option.enable_auto_exposure, False)
            ##set exposure
            color_sensor.set_option(rs.option.exposure, value = 400)
            ##set gain
            #color_sensor.set_option(rs.option.gain, value = 6)
            ##set white balance
            #color_sensor.set_option(rs.option.white_balance, value = 4600)
            #set sharpness
            color_sensor.set_option(rs.option.sharpness, value = 50)
            color_sensor.set_option(rs.option.brightness, value = 5)
        if j == 100:
            cv2.imwrite('laser_test.png', color_image)

        j += 1
        cv2.imshow('RealSense', color_image)
        #cv2.imshow('RealSense', depth_image)
        cv2.waitKey(1)
except Exception as e:
    print(e)
finally:
    pipeline.stop()
