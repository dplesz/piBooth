import picamera
import time
import os
import json
import pygame
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import traceback

prev_button_status = False
time_pressed = 0
taking_pictures = False
button_pin = 17
num_pictures = 1
first_delay = 5
following_delay = 5
screen_width = 1920
screen_height = 1080
overlay_renderer = None
text_color = None
text_font = None
messages = []


def setup_directories():
    file_list = os.listdir('.')
    if 'pbSettings.json' not in file_list:
        f = open('pbsettins.json', 'w+')
        f.write('{}')
        f.close()
    if 'images' not in file_list:
        os.mkdir('images', 0o777)
    if 'sounds' not in file_list:
        os.mkdir('sounds', 0o777)


def on_button_down():
    global prev_button_status
    if not prev_button_status:
        prev_button_status = True


def on_button_up():
    global prev_button_status
    if prev_button_status and not taking_pictures:
        prev_button_status = False
        take_pictures()


def take_pictures():
    global taking_pictures
    taking_pictures = True
    for i in range(0, first_delay):
        add_preview_overlay(20, 200, 55, str(first_delay - i))
        time.sleep(1)
    for i in range(0, num_pictures):
        capture_picture()
        if i < (num_pictures - 1):
            for j in range(0, following_delay):
                add_preview_overlay(20, 200, 55, str(following_delay - j))
                time.sleep(1)
    add_preview_overlay(20, 200, 55, 'Press red button to begin!')
    taking_pictures = False


def import_settings():
    global button_pin, first_delay, following_delay, num_pictures, screen_width,\
        screen_height, text_color, text_font, messages
    try:
        configFile = open('pbSettings.json')
        settings = json.load(configFile)

        def maybe_get_value(dictionary, key, default):
            if key in dictionary:
                return dictionary[key]
            else:
                return default

        # Just in case we don't have the groups set up correctly in the config file
        if 'camera' not in settings: settings['camera'] = {}
        if 'crop' not in settings['camera']: settings['camera']['crop'] = []
        if 'pictures' not in settings: settings['pictures'] = {}
        if 'screen' not in settings: settings['screen'] = {}
        if 'text' not in settings: settings['text'] = {}
        if 'color' not in settings['text']: settings['text']['color'] = []
        if 'messages' not in settings: settings['messages'] = []

        # set program settings
        button_pin = maybe_get_value(settings, 'button_pin', 17)
        num_pictures = maybe_get_value(settings['pictures'], 'num_pictures', 1)
        first_delay = maybe_get_value(settings['pictures'], 'first_delay', 5)
        following_delay = maybe_get_value(settings['pictures'], 'following_delay', 5)
        screen_width = maybe_get_value(settings['screen'], 'width', 1920)
        screen_height = maybe_get_value(settings['screen'], 'height', 1080)
        text_color = (maybe_get_value(settings['text']['color'], 0, 255),
                      maybe_get_value(settings['text']['color'], 1, 40),
                      maybe_get_value(settings['text']['color'], 2, 147),
                      maybe_get_value(settings['text']['color'], 3, 255))
        text_font = maybe_get_value(settings['text'], 'font', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf')
        
        # setup and load sounds
        os.chdir('sounds')
        for i in range(0, len(settings['messages'])):
            m = settings['messages'][i]
            if 'sound' in m and 'text' in m:
                messages.append({'text': m['text'], 'sound': m['sound']})
                pygame.mixer.music.load(m['sound'])
        os.chdir('..')

        # set PiCamera settings.
        camera.resolution = (maybe_get_value(settings['camera'], 'image_width', 1920),
                             maybe_get_value(settings['camera'], 'image_height', 1080))
        camera.framerate = maybe_get_value(settings['camera'], 'framerate', 24)
        camera.sharpness = maybe_get_value(settings['camera'], 'sharpness', 0)
        camera.contrast = maybe_get_value(settings['camera'], 'contrast', 0)
        camera.brightness = maybe_get_value(settings['camera'], 'brightness', 50)
        camera.saturation = maybe_get_value(settings['camera'], 'saturation', 0)
        camera.ISO = maybe_get_value(settings['camera'], 'ISO', 0)
        camera.video_stabilization = maybe_get_value(settings['camera'], 'video_stabilization', False)
        camera.exposure_compensation = maybe_get_value(settings['camera'], 'exposure_compensation', 0)
        camera.exposure_mode = maybe_get_value(settings['camera'], 'exposure_mode', 'auto')
        camera.meter_mode = maybe_get_value(settings['camera'], 'meter_mode', 'average')
        camera.awb_mode = maybe_get_value(settings['camera'], 'awb_mode', 'auto')
        camera.image_effect = maybe_get_value(settings['camera'], 'image_effect', 'none')
        camera.color_effects = maybe_get_value(settings['camera'], 'color_effects', None)
        camera.rotation = maybe_get_value(settings['camera'], 'rotation', 0)
        camera.hflip = maybe_get_value(settings['camera'], 'hflip', False)
        camera.vflip = maybe_get_value(settings['camera'], 'vflip', False)
        camera.crop = (maybe_get_value(settings['camera']['crop'], 0, 0.0),
                       maybe_get_value(settings['camera']['crop'], 1, 0.0),
                       maybe_get_value(settings['camera']['crop'], 2, 1.0),
                       maybe_get_value(settings['camera']['crop'], 3, 1.0))
    except BaseException as err:
        
        traceback.print_exc()
        traceback.print_stack()
    finally:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def capture_picture():
    os.chdir('images')
    imageTime = time.strftime('%Y-%m-%d-%H-%M-%S')
    imageName = 'Image{}.jpg'.format(imageTime)
    camera.capture(imageName)
    os.chdir('..')

def add_preview_overlay(xcoord, ycoord, fontSize, overlayText):
    global overlay_renderer
    img = Image.new('RGBA', (screen_width, screen_height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.font = ImageFont.truetype(
        text_font, fontSize)
    draw.text((xcoord, ycoord), overlayText, text_color)

    # remove overlay before adding a new one -- help keep layers in check.
    if overlay_renderer:
        camera.remove_overlay(overlay_renderer)

    overlay_renderer = camera.add_overlay(img.tobytes(),
                                          layer=3,
                                          size=img.size,
                                          format='rgba');


def clean_up():
    GPIO.cleanup()
    if overlay_renderer:
        camera.remove_overlay(overlay_renderer)
    camera.close()


with picamera.PiCamera() as camera:
    try:
        pygame.mixer.init()
        setup_directories()
        import_settings()
        camera.start_preview()
        # the screen is likely not the size of the display, so crop it to fit
        # camera.preview.crop = (320, 420, screen_width, screen_height)
        camera.preview.fullscreen = True
        # camera.preview.window = (0,0,screen_width,screen_height)
        add_preview_overlay(20, 200, 80, 'Press red button to begin!')
        while True:
            inputState = GPIO.input(button_pin)
            if inputState:
                on_button_down()
            else:
                on_button_up()
    except BaseException as err:
        print('Error: {}'.format(err))
    finally:
        clean_up()
