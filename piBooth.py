import picamera
import time
import os
import json
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

prevButtonStatus = False
timePressed = 0
takingPictures = False
button_pin = 17
num_pictures = 1
first_delay = 5
following_delay = 5
screen_width = 1920
screen_height = 1080
overlay_renderer = None

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
    for i in range(0,first_delay):
        addPreviewOverlay(20,200,55,str(first_delay-i))
        time.sleep(1)
    #time.sleep(first_delay)
    for i in range(0,num_pictures):
        capturePicture()
        if i < (num_pictures - 1):
            for j in range(0,following_delay):
                addPreviewOverlay(20,200,55,str(following_delay-j))
                time.sleep(1)
    addPreviewOverlay(20,200,55,"Press red button to begin!")
    takingPictures = False

def importSettings():
    global button_pin, first_delay, following_delay, num_pictures, screen_width, screen_height
    try:
        configFile = open('pbSettings.json')
        settings = json.load(configFile)
        
        def maybeGetValue(dictionary,key,default):
            if key in dictionary:
                return dictionary[key]
            else:
                return default
           
        # set program settings
        button_pin = maybeGetValue(settings,"button_pin",17)
        num_pictures = maybeGetValue(settings["pictures"],"num_pictures",1)
        first_delay = maybeGetValue(settings["pictures"],"first_delay",5)
        following_delay = maybeGetValue(settings["pictures"],"following_delay",5)
        screen_width = maybeGetValue(settings["screen"],"width",1920)
        screen_height = maybeGetValue(settings["screen"],"height",1080)

        
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

def addPreviewOverlay(xcoord,ycoord,fontSize,overlayText):
    global overlay_renderer
    img = Image.new("RGB", (screen_width, screen_height))
    draw = ImageDraw.Draw(img)
    draw.font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",fontSize)
    draw.text((xcoord,ycoord), overlayText, (255, 20, 147))
    print("addPreview {}",overlayText)

    if overlay_renderer:
        camera.remove_overlay(overlay_renderer)
    overlay_renderer = camera.add_overlay(img.tobytes(),
                                              layer=3,
                                              size=img.size,
                                              format='rgb',
                                              alpha=128);

def cleanUp():
    GPIO.cleanup()
    if overlay_renderer:
        camera.remove_overlay(overlay_renderer)
    camera.close()
    
with picamera.PiCamera() as camera:
    try:
        importSettings()
        camera.start_preview()
        # the screen is likely not the size of the display, so crop it to fit
        camera.preview.crop = (320,420,screen_width,screen_height)
        addPreviewOverlay(20,200,55,"Press red button to begin!")
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
