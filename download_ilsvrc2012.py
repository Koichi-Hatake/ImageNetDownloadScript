#
# Copyright (C) 2018 Koichi Hatakeyama
# All rights reserved.
#
import argparse
import datetime
import os
import signal
import sys
import threading
import logging
from glob import glob
from pathlib import Path
from socket import timeout
import pandas as pd
import urllib.error
import urllib.request

# Pre defined constants
TARGET_IMAGE_DIR = 'master_images2'
URL_LIST_FILE = 'urllist.txt'
MAX_THREAD_NUM = 16
MAX_TASK_QUEUE_SIZE = 1024
START_ROW_CNT = 0

# Logging
logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s')

class WorkerThread(threading.Thread):
    
    def __init__(self, name, channel):
        super(WorkerThread, self).__init__()
        self.channel = channel
        self.shutdownRequested = False

    def shutdownRequest(self):
        self.shutdownRequested = True
        
    def doShutdown(self):
        logging.debug('stopped.')

    def run(self):
        while True:
            self.request = self.channel.takeRequest()
            if (self.request is None):
                break
            if (self.request.isFinishBall()):
                self.channel.stopWorkers()
                break
            self.request.execute()
            if(self.shutdownRequested):
                break

        self.doShutdown()
        

class Channel(object):

    def __init__(self, thread_num, queue_size):
        self.head = 0
        self.tail = 0
        self.count = 0
        self.threads = thread_num
        self.queue_size = queue_size
        self.max_task_num = 0
        self.cond = threading.Condition()
        self.isFinished = False
        self.requestQueue = [0 for i in range(self.queue_size)]
        self.threadPool = []
        self.totalProcessedTaskNum = START_ROW_CNT

        for i in range(self.threads):
            t = WorkerThread("Worker-" + str(i), self)
            self.threadPool.append(t)

    def setMaxTaskNum(self, max_task_num):
        self.max_task_num = max_task_num

    def startWorkers(self):
        for i in range(self.threads):
            self.threadPool[i].start()

    def putRequest(self, request):
        with self.cond:
            while (self.count >= self.queue_size):
                self.cond.wait()

            self.requestQueue[self.tail] = request
            self.tail = (self.tail + 1) % len(self.requestQueue)
            self.count += 1
            self.cond.notifyAll()

    def takeRequest(self):
        with self.cond:
            while (self.count <= 0):
                self.cond.wait()
                if (self.isFinished):
                    return None
            request = self.requestQueue[self.head]
            self.head = (self.head + 1) % len(self.requestQueue)
            self.count -= 1
            self.cond.notifyAll()
            self.totalProcessedTaskNum += 1
            print("Processing: " + str(self.totalProcessedTaskNum) + " / " + str(self.max_task_num))
            return request

    def stopWorkers(self):
        self.isFinished = True
        logging.debug('Stopping all wokers...')
        for i in range(self.threads):
            self.threadPool[i].shutdownRequest()
        with self.cond:
            self.cond.notifyAll()

        
class ParseRequest(object):
    def __init__(self, name):
        self.name = name

    def execute(self):
        logging.debug('execute %s', "[ Request from " + self.name + " ]")

    def getName(self):
        return self.name

    def isFinishBall(self):
        return False

class FinishBall(ParseRequest):
    TASK_NAME = 'Finalize Request'

    def __init__(self):
        super().__init__(self.TASK_NAME)
        
    def isFinishBall(self):
        return True

    
class DownloadImageFile(ParseRequest):
    TASK_NAME = 'Download Image'
    
    def __init__(self, url, target_image_path):
        super().__init__(self.TASK_NAME)
        self.url = url
        self.image_path = target_image_path
        
    def execute(self):
        # Download image
        if(self.image_path.exists()):
            logging.debug('Skip %s', str(self.image_path))
            return

        logging.debug('Processing %s', str(self.image_path))
        try:
            data = urllib.request.urlopen(self.url).read()
            with open(self.image_path, mode="wb") as f:
                f.write(data)
#        except urllib.error.HTTPError as eh:
#            print(eh)
#        except urllib.error.URLError as eu:
#            print(eu)
#        except urllib.error.ContentTooShortError as ec:
#            print(ec)
#        except UnicodeEncodeError as ee:
#            print(ee)
#        except timeout as et:
#            print(et)
        except Exception as e:
            logging.debug(e)
            
class TaskProducerThread(threading.Thread):

    def __init__(self, channel, dest_img_dir, url_list_file):
        super(TaskProducerThread, self).__init__()
        self.channel = channel
        self.target_dir = dest_img_dir
        self.url_list_file = url_list_file
        self.start_time = datetime.datetime.now()

    def run(self):
        # Read URL file
        url_df = pd.read_csv(self.url_list_file, sep=' ', names=('target_file', 'url'))
        row, col = url_df.shape
        self.channel.setMaxTaskNum(row)
        print("URL lines: " + str(row))

        # Process each URLs
        for i in range(START_ROW_CNT, row):
            save_filename = Path(url_df.iat[i, 0]).name
            url = url_df.iat[i, 1].replace("\"", "")
            #print("File: " + save_filename)
            #print("  URL: " + url)
            save_file_path = Path(self.target_dir, save_filename)
            req = DownloadImageFile(url, save_file_path)
            self.channel.putRequest(req)
            
        # Finlize
        finish_ball = FinishBall()
        self.channel.putRequest(finish_ball)

        # Process time
        elapsed_time = datetime.datetime.now() - self.start_time
        print ("############\nElapsed_time: " + str(elapsed_time) + "\n############\n")
            
def parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Download ILSVRC2012 image files. r0.01')
    parser.add_argument('--target', '-t', default=TARGET_IMAGE_DIR, help='Specify target directory for images')
    parser.add_argument('--url_list', '-u', default=URL_LIST_FILE, help='Specify URL list file')
    parser.add_argument('--thread_num', '-j', default=MAX_THREAD_NUM, type=int, help='Specify num of threads')

    return parser.parse_args()

def sigint_handler(signal, frame):
    logging.debug('Caught Ctrl-C!')
    func = frame.f_locals['self']
    func.channel.stopWorkers()

def main():

    # Parse arguments
    args = parse_args()
    target_dir = args.target
    url_list = args.url_list
    thread_num = args.thread_num

    # Destination directory check
    dest_img_dir = Path(target_dir)
    if(not dest_img_dir.exists()):
        print("Create dir: " + str(dest_img_dir))
        dest_img_dir.mkdir(parents=True, exist_ok=True)

    # URL list file check
    url_list_file = Path(url_list)
    if(not url_list_file.exists()):
        print("No such dir: " + str(url_list_file))
        sys.exit()

    # Ctrl-C signal handler
    signal.signal(signal.SIGINT, sigint_handler)

    # Create thread
    channel = Channel(thread_num, MAX_TASK_QUEUE_SIZE)
    channel.startWorkers()

    # Invoke Task thread
    task_thread = TaskProducerThread(channel, dest_img_dir, url_list_file)
    task_thread.start()
    task_thread.join()
    

if __name__ == '__main__':
    main()

# EOF
