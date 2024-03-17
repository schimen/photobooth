# Photobooth project

This is a photobooth project for my birthday celebration.
The concept of the project is a dslr camera connected to a respberry pi which captures four images with it and put them together in a single image. The image is then Sent to a small photo printer that prints the image.
Here is an illustration of the concept:
![illustration of concept](./example_images/concept_illustration.png)
Here is an example of a possible resulting image:
![result example](./example_images/montage_example.jpg)

### Technical details

I use a Canon dslr that I can connect to a Raspberry Pi via Python bindings for [gphoto2](http://gphoto.org/). The Python program running on the Raspberry Pi is [photobooth.py](./photobooth.py). The rasbperry pi will connect to a photo printer that prints the montage image when it is finished.

### Requirements

**Python**
- [pillow](https://pypi.org/project/pillow/)
- [gphoto2](https://pypi.org/project/gphoto2/)

**Hardware**
- A camera
(prefereably with flash and on wall power)
- A computer
(preferably a small Linux computer like a Raspberr Pi)
- A keyboard or button and that can tell the computer when to take an image
- A screen or led that indicates when images will be taken
- A printer that the computer can control

**Here is an image of the button and led connected to the raspberry pi**
![raspberry pi connection diagram](./example_images/schematic.png)