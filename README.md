# ImageNetDownloadScript
This series of scripts are to download ILSVRC 2012 images files one by one.  
http://image-net.org/challenges/LSVRC/2012/

## Description
These scripts will be used when you will download all ILSVRC image files one by one. There are several pre-conditions to use these scripts so please read this README carefully. And not only downloading but ... 

## Requirement
1. aaa
1. bbb

## Usage
1. Download scripts  
```$ python download_ilsvrc2012.py [] ```  
This script download all image files that described in urllist.txt to a specific directory.  

1. Move error files
  ```
$ python remove_err_img.py [-h] [--img_dir IMG_DIR] [--err_img_dir ERR_IMG_DIR]
optional arguments:  
     -h, --help           show this help message and exit  
     -i, --img_dir        Specify image directory
     -e, --err_img_dir    Specify destination directoryfor error file
```
    
This script move following type of error files to a specific directory.
   - Zero size files
   - Flickr error file
   - Invalid image format file
   - Mono image file  
   


1. 


## License
This software includes the work that is distributed in the Apache License 2.0

## Author
[Koichi-Hatake] (https://github.com/DeepLearningAndroid)
