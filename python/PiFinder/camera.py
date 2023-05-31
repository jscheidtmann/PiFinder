#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
This module is the camera
* Captures images
* Places preview images in queue
* Places solver images in queue
* Takes full res images on demand

"""
import os
import queue
import time

from PIL import Image, ImageDraw, ImageFont, ImageChops

# from picamera2 import Picamera2

from PiFinder import config
from PiFinder import utils


exposure_time = None
analog_gain = None


def get_images(
    shared_state, camera_hardware, camera_image, command_queue, console_queue, cfg
):
    global exposure_time, analog_gain
    debug = False
    camera = camera_hardware

    exposure_time = cfg.get_option("camera_exp")
    analog_gain = cfg.get_option("camera_gain")
    screen_direction = cfg.get_option("screen_direction")

    # Set path for test images
    root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    test_image_path = os.path.join(root_dir, "test_images", "pifinder_debug.png")

    # 60 half-second cycles
    sleep_delay = 60
    while True:
        imu = shared_state.imu()
        if shared_state.power_state() == 0:
            time.sleep(0.5)

            # Even in sleep mode, we want to take photos every
            # so often to update positions
            sleep_delay -= 1
            if sleep_delay > 0:
                continue
            else:
                sleep_delay = 60

        if imu and imu["moving"] and imu["status"] > 0:
            pass
        else:
            image_start_time = time.time()
            if not debug:
                base_image = camera.capture()
                base_image = base_image.convert("L")
                if screen_direction == "right":
                    base_image = base_image.rotate(90)
                else:
                    base_image = base_image.rotate(270)
            else:
                # load image and wait
                base_image = Image.open(test_image_path)
                time.sleep(1)
            # check imu to make sure we're still static
            imu = shared_state.imu()
            if imu and imu["moving"] and imu["status"] > 0:
                pass
            else:
                camera_image.paste(base_image)
                shared_state.set_last_image_time((image_start_time, time.time()))
        command = True
        while command:
            try:
                command = command_queue.get(block=False)
            except queue.Empty:
                command = ""

            if command == "debug":
                if debug:
                    debug = False
                else:
                    debug = True

            if command.startswith("set_exp"):
                exposure_time = int(command.split(":")[1])
                camera.set_camera_config(exposure_time, analog_gain)
                console_queue.put("CAM: Exp=" + str(exposure_time))

            if command.startswith("set_gain"):
                analog_gain = int(command.split(":")[1])
                exposure_time, analog_gain = camera.set_camera_config(
                    exposure_time, analog_gain
                )
                console_queue.put("CAM: Gain=" + str(analog_gain))

            if command == "exp_up" or command == "exp_dn":
                if command == "exp_up":
                    exposure_time = int(exposure_time * 1.25)
                else:
                    exposure_time = int(exposure_time * 0.75)
                camera.set_camera_config(exposure_time, analog_gain)
                console_queue.put("CAM: Exp=" + str(exposure_time))
            if command == "exp_save":
                console_queue.put("CAM: Exp Saved")
                cfg.set_option("camera_exp", exposure_time)
                cfg.set_option("camera_gain", int(analog_gain))

            if command.startswith("save"):
                filename = command.split(":")[1]
                filename = f"{utils.data_dir}/captures/{filename}.png"
                camera.capture_file(filename)
                console_queue.put("CAM: Saved Image")

            if command.startswith("save_hi"):
                # Save high res image....
                filename = command.split(":")[1]
                filename = f"{utils.data_dir}/captures/{filename}.png"
                # set_camera_highres(camera)
                camera.capture_file(filename)
                console_queue.put("CAM: Saved Hi Image")
                # set_camera_defaults(camera)
