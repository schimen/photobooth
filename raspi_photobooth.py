"""
This python script is intended to run on a raspberry pi with a button, led 
and camera connected. The camera should be compatible with gphoto2.
This script waits for a button press and starts the `create_image` function 
from the photooth.py file when a button press is registered.
"""

from time import sleep, time
import threading
import logging as log
import atexit
import subprocess
from RPi import GPIO
from photobooth import create_image

photobooth_mutex = threading.Lock()
BUTTON = 23
LED = 24
PRINTER_MAC = '01:23:45:67:89:AB'
PRINTER_RES = (int(3.4 * 800), int(2.3 * 800))

import logging as log
import subprocess


def print_image(path: str, addr: str) -> None:
    """
    Send image to bluetooth printer via `obexftp`.
    `path` is path to image that will be printed.
    `addr` is mac address to bluetooth printer. 
    """
    command = f'obexftp -S -H -U none -B 4 -b {addr} -p {path}'
    log.debug('Printing with command: %s', command)
    subprocess.run(command, shell=True)


def blink(period: int) -> None:
    """
    Blink led for a total period of time specified in `period` argument
    """
    GPIO.output(LED, GPIO.HIGH)
    sleep(period / 2)
    GPIO.output(LED, GPIO.LOW)
    sleep(period / 2)


def countdown_handler(wait_time: int) -> None:
    """
    Blink with increasing frequency before a new image is taken
    """
    max_period = 1
    min_period = 0.05
    start = time()
    time_left = wait_time
    while time() - start < wait_time:
        time_left = wait_time - (time() - start)
        period = time_left / 4
        if period < min_period:
            period = min_period
        elif period > max_period:
            period = max_period

        blink(period)


def run_photobox(mutex: threading.Lock) -> None:
    """
    Run `create_image` function and release mutex after it is finished
    """
    log.debug('Creating photobox image')
    try:
        blink(1)
        path = create_image(countdown_handler=countdown_handler,
                            dimensions=PRINTER_RES)
        if path is not None:
            log.debug('Printing image')
            print_image(path, PRINTER_MAC)
        else:
            log.warning('Path to print image is None, could not print image')

        print_image(path, PRINTER_MAC)
        blink(0.1)
        blink(0.1)
    finally:
        mutex.release()


def button_handler(_):
    """
    Callback function for every time the buton is pressed
    """
    log.debug('Button pressed')
    if photobooth_mutex.acquire(blocking=False):
        # Create image in thread
        threading.Thread(target=run_photobox,
                         args=(photobooth_mutex, )).start()

    else:  # Don't start a new thread if the previous is still running
        log.debug('Could not start photobooth thread, mutex busy')


def main():
    # Setup gpio
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
    GPIO.add_event_detect(BUTTON,
                          GPIO.FALLING,
                          callback=button_handler,
                          bouncetime=100)
    atexit.register(GPIO.cleanup)

    # Blink when starting program
    log.debug("Starting program")
    blink(0.1)
    blink(0.1)

    # Run infinite loop
    while True:
        sleep(5)


if __name__ == '__main__':
    log.basicConfig(format='%(levelname)s: %(message)s', level=log.INFO)
    main()
