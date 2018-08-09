import picamera
import time
import os
import json
import RPi.GPIO as GPIO

prevButtonStatus = False
timePressed = 0
takingPictures = False
button_pin = 17
num_pictures = 1
first_delay = 5
following_delay = 5

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
    time.sleep(first_delay)
    for i in range(0,num_pictures):
        capturePicture()
        if i < (num_pictures - 1):
            time.sleep(following_delay)
    takingPictures = False

def importSettings():
    global button_pin, first_delay, following_delay, num_pictures
    try:
        configFile = open('pbSettings.json')
        settings = json.load(configFile)
        
        def maybeGetValue(dictionary,key,default):
            if key in dictionary:
                return dictionary[key]
            else:
                return default
           
        # set program settings
        button_pin = settings["button_pin"] or 17
        num_pictures = settings["pictures"]["num_pictures"] or 1
        first_delay = settings["pictures"]["first_delay"] or 5
        following_delay = settings["pictures"]["following_delay"] or 5
        
        # set PiCamera settings.
        camera.resolution = (maybeGetValue(settings["camera"],"image_width",1920),
                             maybeGetValue(settings["camera"],"image_height",1080))
        camera.framerate = maybeGetValue(settings["camera"],"framerate",24)
        camera.sharpness = maybeGetValue(settings["camera"],"sharpness",0)
        camera.contrast = maybeGetValue(settings["camera"],"contrast",0)
        camera.brightness = maybeGetValue(settings["camera"],"brightness",50)
        camera.saturation = maybeGetValue(settings["camera"],"saturation",0)
        camera.ISO = maybeGetValue(settings["camera"],"ISO",0)
        camera.video_stabilization = maybeGetValue(settings["camera"],"video_stabilization",False)
        camera.exposure_compensation = maybeGetValue(settings["camera"],"exposure_compensation",0)
        camera.exposure_mode = maybeGetValue(settings["camera"],"exposure_mode",'auto')
        camera.meter_mode = maybeGetValue(settings["camera"],"meter_mode",'average')
        camera.awb_mode = maybeGetValue(settings["camera"],"awb_mode",'auto')
        camera.image_effect = maybeGetValue(settings["camera"],"image_effect",'none')
        camera.color_effects = maybeGetValue(settings["camera"],"color_effects",None)
        camera.rotation = maybeGetValue(settings["camera"],"rotation",0)
        camera.hflip = maybeGetValue(settings["camera"],"hflip",False)
        camera.vflip = maybeGetValue(settings["camera"],"vflip",False)
        camera.crop = (maybeGetValue(settings["camera"]["crop"],0,0.0),
                       maybeGetValue(settings["camera"]["crop"],1,0.0),
                       maybeGetValue(settings["camera"]["crop"],2,1.0),
                       maybeGetValue(settings["camera"]["crop"],3,1.0))
    except BaseException as err:
        print("Import Error: {}".format(err))
    finally:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(button_pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
           
def capturePicture():
    imageTime = time.strftime("%Y-%m-%d-%H-%M-%S")
    imageName = "Image{}.jpg".format(imageTime)
    camera.capture(imageName)
    
def cleanUp():
    GPIO.cleanup()
    camera.close()
    
with picamera.PiCamera() as camera:
    try:
        importSettings()
        camera.start_preview()
        while True:
            inputState = GPIO.input(button_pin)
            if inputState == True:
                onButtonDown()
            else:
                onButtonUp()
    except BaseException as err:
        print("Error: {}".format(err))
    finally:
        cleanUp()
