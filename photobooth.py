"""
This python file provides functionality to capture images via the `gphoto2` 
library and paste them together in another image using the `pillow` library.
The relevant functions are:
- `capture_images`
- `create_montage`
- `create_image`
"""

import os
from time import sleep
import threading
from datetime import datetime
import logging as log
from typing import Callable, List, Tuple
from PIL import Image
import gphoto2 as gp


def open_camera() -> gp.Camera:
    """
    Connect to a camera via gphoto2 and return the Camera object.
    Return None if no camera was available.
    """
    try:
        camera = gp.Camera()
        camera.init()
        return camera
    except gp.GPhoto2Error as err:
        log.error('%s, please connect a compatible camera', err)
        return None


def capture_images(
        camera: gp.Camera,
        n_images: int = 4,
        wait_time: int = 0,
        outdir: str = 'output',
        countdown_handler: Callable[[int], None] = None) -> List[str]:
    """
    Capture and download images with a camera and return the paths of each 
    image in a list.
    Use `countdown_handler` to specify a handler function called when sleeping 
    before image capture. The `wait_time` argument will be added as an
    argument to `countdown_handler`.
    """
    # Capture n images
    image_paths = []
    for i in range(n_images):
        # Sleep if specified
        if wait_time > 0:
            log.debug('Waiting %d s before capture', wait_time)
            # Start countdown handler in thread
            if callable(countdown_handler):
                threading.Thread(target=countdown_handler,
                                 args=(wait_time, )).start()
            sleep(wait_time)

        log.debug('Capturing image %d of %d', i + 1, n_images)
        # Capture image
        try:
            file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
        except gp.GPhoto2Error as e:
            log.error('Could not capture image, %s', e)
            continue

        # Get image from camera
        try:
            camera_file = camera.file_get(file_path.folder, file_path.name,
                                          gp.GP_FILE_TYPE_NORMAL)
        except gp.GPhoto2Error as e:
            log.error('%s, could not get file %s in %s from camera', e,
                      file_path.name, file_path.folder)
            continue

        # Save file
        filename = datetime.now().strftime(
            r'%y-%m-%d_%H-%M-%S') + f'_capture-{i}.jpg'
        path = os.path.join(outdir, filename)
        camera_file.save(path)
        image_paths.append(path)
        log.info('Saved capture in %s', path)

    camera.exit()
    return image_paths


def paste_images(base_image: Image, paths: List[str],
                 shape: Tuple[int, int]) -> Image:
    """
    Calculate position and size for each image in paths and paste it on base_image
    """
    # Rotate if there are more columns than rows
    rows, cols = shape
    if cols > rows:
        base_image = base_image.rotate(90, expand=True)

    # Calculate width, height, aspect ratio and border offset
    width, height = base_image.size
    offset = int(width / 100)
    max_img_w = int((width - (rows + 1) * offset) / rows)
    max_img_h = int((height - (cols + 1) * offset) / cols)
    aspect_ratio = width / height

    # Go through all image files
    for i, path in enumerate(paths):
        # Read image and put it on base image
        with Image.open(path) as img:
            # Resize with correct aspect ratio
            img_w, img_h = img.size
            img_ar = img_w / img_h
            if img_ar > aspect_ratio:
                new_size = (max_img_w, int(max_img_w / img_ar))
            else:
                new_size = (int(max_img_h * img_ar), max_img_h)

            img = img.resize(new_size)

            # Calculate x and y offset values
            img_w, img_h = img.size

            # Paste image onto base image
            pos_x = offset + (i % rows) * (max_img_w + offset)
            pos_y = offset + (i // rows) * (max_img_h + offset)
            base_image.paste(img, (pos_x, pos_y))

    return base_image


def create_montage(paths: List[str],
                   dimensions: Tuple[int, int] = (1500, 1000),
                   background: str = None) -> Image:
    """
    Take a list of image paths and put them together in a montage with 
    the `paste_images` function.
    Use `background` to set background image, or use `dimensions` to use a 
    white background image of the dimensions.
    """
    # Create base image
    if background is None:
        base_image = Image.new('RGB', dimensions, color=(255, 255, 255))
    else:
        base_image = Image.open(background)

    # Check that the amount images is supported in layout
    n_images = len(paths)
    n_image_layout = {
        1: (1, 1),
        4: (2, 2),
        9: (3, 3),
    }
    if n_images not in n_image_layout:
        log.error('Got %d images, but only %s amount of images are supported.',
                  n_images, str(n_image_layout.keys()))
        return None

    return paste_images(base_image, paths, n_image_layout[n_images])


def create_image(
    outdir: str = 'output',
    background: str = None,
    dimensions: Tuple[int, int] = (1500, 1000),
    countdown_handler: Callable[[int], None] = None,
) -> str:
    """
    Take photos with `capture_images` command and put them in a montage image.
    Returns the path of the montage image.
    """
    # Create output dir if it does not exist
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # Open camera
    camera = open_camera()
    if camera is None:
        log.error('No camera available')
        return

    # Capture the images
    image_paths = capture_images(camera,
                                 wait_time=2,
                                 outdir=outdir,
                                 countdown_handler=countdown_handler)
    if len(image_paths) < 1:
        log.error('Got no image paths when capturing images')
        return

    # Create an image with the capture images gathered and save it
    image = create_montage(image_paths,
                           background=background,
                           dimensions=dimensions)
    if image is None:
        log.error('Could not create montage image')
        return
    filename = datetime.now().strftime(r'%y-%m-%d_%H-%M-%S') + '_montage.jpg'
    result_image_path = os.path.join(outdir, filename)
    image.save(result_image_path)
    log.info('Saved image montage in %s', result_image_path)
    return result_image_path


def main():
    prompt = 'Press enter to capture photos. Type q and enter to quit\n> '
    while 'q' not in input(prompt).lower():
        create_image()


if __name__ == '__main__':
    log.basicConfig(format='%(levelname)s: %(message)s', level=log.INFO)
    main()
