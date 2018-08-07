import picamera
import time
import os
import json
import RPi.GPIO as GPIO

BUTTON_PIN = 17
NUM_PICTURES_TO_TAKE = 1
BUTTON_MASH_TIME = 5
FIRST_PIC_DELAY = 5
FOLLOWING_PIC_DELAY = 5
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
IMAGE_WIDTH = 2592
IMAGE_HEIGHT = 1944
WORKING_DIR = "/home/pi"

prevButtonStatus = False
timePressed = 0
takingPictures = False

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#def notButtonMashed:
#    return time.time() - timePressed > BUTTON_MASH_TIME

def onButtonDown():
    global prevButtonStatus
    if (prevButtonStatus == False):
        prevButtonStatus = True

def onButtonUp():
    global prevButtonStatus
    if ((prevButtonStatus == True) and
        not takingPictures):
        prevButtonStatus = False
        takePictures()
        
def takePictures():
    global takingPictures
    takingPictures = True
    time.sleep(FIRST_PIC_DELAY)
    for i in range(0,NUM_PICTURES_TO_TAKE):
        capturePicture()
        time.sleep(FOLLOWING_PIC_DELAY)
    takingPictures = False
    
def initCamera(camera):
    #camera settings
    camera.resolution            = (SCREEN_WIDTH, SCREEN_HEIGHT)
    camera.framerate             = 24
    camera.sharpness             = 0
    camera.contrast              = 0
    camera.brightness            = 50
    camera.saturation            = 0
    camera.ISO                   = 0
    camera.video_stabilization   = False
    camera.exposure_compensation = 0
    camera.exposure_mode         = 'auto'
    camera.meter_mode            = 'average'
    camera.awb_mode              = 'auto'
    camera.image_effect          = 'none'
    camera.color_effects         = None
    camera.rotation              = 0
    camera.hflip                 = False
    camera.vflip                 = False
    camera.crop                  = (0.0, 0.0, 1.0, 1.0)
            
def capturePicture():
    imageTime = time.strftime("%Y-%m-%d-%H-%M-%S")
    imageName = "Image{}.jpg".format(imageTime)
    camera.capture(imageName,resize=(IMAGE_WIDTH,IMAGE_HEIGHT))
    
def cleanUp():
    GPIO.cleanup()
    camera.close()

with picamera.PiCamera() as camera:
    try:
        os.chdir(WORKING_DIR)
        initCamera(camera)
        camera.start_preview()
        while True:
            inputState = GPIO.input(BUTTON_PIN)
            if inputState == True:
                onButtonDown()
            else:
                onButtonUp()
    except BaseException as err:
        print("Error: {}".format(err))
        cleanUp()
    finally:
        cleanUp()
        
