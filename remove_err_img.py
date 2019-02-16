#
# Copyright (C) 2018 Koichi Hatakeyama
# All rights reserved.
#

# This script remove following error type image files.
#  1. Zero file size
#  2. Flickr error image
#  3. Invalid image
#  4. Mono image

import argparse
import datetime
import hashlib
import numpy as np
import os
import re
import sys
from glob import glob
from pathlib import Path
from PIL import Image

# Pre defined constants
IMG_DIR = 'master_images2'
ERR_IMG_DIR = 'err_imgs2'
FLICKER_ERR_IMG_HASH = '880a7a58e05d3e83797f27573bb6d35c'
FLICKER_ERR_IMG_SIZE = 2051

def process_err_img(err_img, dest_path):
    print(" Move: " + str(err_img) + " -> " + str(dest_path))
    err_img.rename(dest_path)

def parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Remove error image files r0.01')
    parser.add_argument('--img_dir', '-i', default=IMG_DIR, help='Specify image directory')
    parser.add_argument('--err_img_dir', '-e', default=ERR_IMG_DIR, help='Specify destination directoryfor error file')

    return parser.parse_args()

def main():

    # Start time
    start_time = datetime.datetime.now()

    # Parse arguments
    args = parse_args()
    img_dir = args.img_dir
    err_img_dir = args.err_img_dir

    # Check image directory
    img_path = Path(img_dir)
    if(not img_path.exists()):
        print("No such dir: " + str(img_path))
        sys.exit()

    # Check error image directory
    err_img_path = Path(err_img_dir)
    if(not err_img_path.exists()):
        err_img_path.mkdir(parents=True, exist_ok=True)
    
    # Check all image files
    img_files = img_path.glob("*.jpg")
    #total = len(list(img_files))
    cur = 0
    for file in img_files:

        # Get size and set error image path to move
        img_size = os.path.getsize(file)
        err_img_path = Path(err_img_dir, file.name)

        # Progress
        cur += 1
        print("Processing: " + str(cur))
        
        # 1. Zero file size
        if(img_size == 0):
            print("Found zero size image: " + str(file))
            process_err_img(file, err_img_path)
            continue
        
        # 2. Flickr error image
        if(img_size == FLICKER_ERR_IMG_SIZE):
            with open(file, 'rb') as image:
                img_md5 = hashlib.md5(image.read()).hexdigest()
                image.close()
                if(img_md5 == FLICKER_ERR_IMG_HASH):
                    print("Found Flickr error img: " + str(file))
                    process_err_img(file, err_img_path)
                    continue

        # 3. Invalid image
        try:
            img = Image.open(file)
            im = np.array(img)
            img.close()
        except:
            print("Image file open error: " + str(file))
            process_err_img(file, err_img_path)
            continue

        # 4. Mono image
        try:
            width, height, col = im.shape
        except:
            print("Image file shape error: " + str(file) + " : " + str(im.shape))
            # This type of image file will be used after resizing.
            #process_err_img(file, err_img_path)
            continue

        if(col != 3):
            print("Image error(mono): " + str(file) + ":" + str(col))
            process_err_img(file, err_img_path)
            continue

    # Process time
    elapsed_time = datetime.datetime.now() - start_time
    print ("############\nElapsed time: " + str(elapsed_time) + "\n############\n")

    
if __name__ == '__main__':
    main()

# EOF
