import gphoto2 as gp
import os
from PIL import Image
from time import sleep
from datetime import datetime
import logging

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger('photobooth')


def capture_images(n_images=4, wait_time=0, outdir='output') -> list:
    """
    Capture and download images with a camera and return the paths of each 
    image in a list
    """
    # Connect to camera
    try:
        camera = gp.Camera()
        camera.init()
    except gp.GPhoto2Error as e:
        log.error('%s, please connect a compatible camera', e)
        return []

    # Capture n images
    image_paths = []
    for i in range(n_images):
        # Sleep if specified
        if wait_time > 0:
            log.debug('Waiting %d s before capture', wait_time)
            sleep(wait_time)

        log.debug('Capturing image %d of %d', i + 1, n_images)
        file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
        camera_file = camera.file_get(file_path.folder, file_path.name,
                                      gp.GP_FILE_TYPE_NORMAL)

        # Save file
        filename = datetime.now().strftime(
            r'%y-%m-%d_%H-%M-%S') + f'_capture-{i}.jpg'
        path = os.path.join(outdir, filename)
        camera_file.save(path)
        image_paths.append(path)
        log.info('Saved capture in %s', path)

    camera.exit()
    return image_paths


def create_image_montage(paths: list,
                         dimensions=(1360, 920),
                         background=None) -> Image:
    """
    Take a list of image paths and put them together in a montage
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
    if n_images not in n_image_layout.keys():
        log.error('Got %d images, but only %s amount of images are supported.',
                  n_images, str(n_image_layout.keys()))
        return None

    # Rotate if there are more columns than rows
    rows, cols = n_image_layout[n_images]
    if cols > rows:
        base_image = base_image.rotate(90, expand=True)

    # Calculate width, height, aspect ratio and border offset
    w, h = base_image.size
    offset = int(w / 100)
    max_img_w = int((w - (rows + 1) * offset) / rows)
    max_img_h = int((h - (cols + 1) * offset) / cols)
    ar = w / h

    # Go through all image files
    for i, path in enumerate(paths):
        # Read image and put it on base image
        with Image.open(path) as img:
            # Resize with correct aspect ratio
            img_w, img_h = img.size
            img_ar = img_w / img_h
            if img_ar > ar:
                new_size = (max_img_w, int(max_img_w / img_ar))
            else:
                new_size = (int(max_img_h * img_ar), max_img_h)

            img = img.resize(new_size)

            # Calculate x and y offset values
            img_w, img_h = img.size
            offset_x = int(img_w * offset / max_img_w)
            offset_y = int(img_h * offset / max_img_h)

            # Paste image onto base image
            pos_x = offset + (i % rows) * (max_img_w + offset_x)
            pos_y = offset + (i // rows) * (max_img_h + offset_y)
            base_image.paste(img, (pos_x, pos_y))

    return base_image


def create_image(outdir='output', background=None) -> str:
    """
    Take photos with `capture_images` command and put them in a montage image.
    Returns the path of the montage image.
    """
    # Create output dir if it does not exist
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # Capture the images
    image_paths = capture_images(wait_time=2, outdir=outdir)
    if len(image_paths) < 1:
        log.error('Got no image paths when capturing images')
        return

    # Create an image with the capture images gathered and save it
    image = create_image_montage(image_paths, background=background)
    if image is None:
        log.error('Could not create montage image')
        return
    filename = datetime.now().strftime(r'%y-%m-%d_%H-%M-%S') + '_montage.jpg'
    result_image_path = os.path.join(outdir, filename)
    image.save(result_image_path)
    log.info('Saved image montage in %s', result_image_path)


if __name__ == '__main__':
    prompt = 'Press enter to capture photos. Type q and enter to quit\n> '
    while 'q' not in input(prompt).lower():
        create_image()
