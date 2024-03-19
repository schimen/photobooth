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
from RPi import GPIO
from photobooth import create_image

photobooth_mutex = threading.Lock()
BUTTON = 23
LED = 24


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
        create_image(countdown_handler=countdown_handler)
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

    else:  # This is my solution to debounce :)
        log.debug('Could not start photobooth thread, mutex busy')


def main():
    # Setup gpio
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
    GPIO.add_event_detect(BUTTON, GPIO.FALLING, callback=button_handler)
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
