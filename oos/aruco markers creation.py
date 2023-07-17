#import opencv
import cv2
import os
from PIL import Image
#generate aruco markers
def generate_aruco_markers():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    downloads_path = os.path.join(r"C:\Users\mathi\Downloads")
    #generate an image with the marker
    imgs = []
    for i in range(4):
        #name_them by their id
        imgs.append(cv2.aruco.generateImageMarker(aruco_dict, i, 200))
    
    #save them to a pdf using PIL
    pdf_path = os.path.join(downloads_path, "aruco_markers.pdf")
    #convert to PIL images
    imgs = [Image.fromarray(img) for img in imgs]
    #save to pdf
    imgs[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=imgs[1:])

generate_aruco_markers()