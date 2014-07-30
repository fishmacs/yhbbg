import os
import shutil

import Image

from django.conf import settings

def resize(srcf, desf, w, h):
    img = Image.open(srcf)
    img = img.resize((w, h), Image.ANTIALIAS)
    img.save(desf)

def prepare_image(image, size):
    local_img = settings.MEDIA_ROOT + image.name
    remote_img = image.path
    if os.path.exists(remote_img) and \
      (not os.path.exists(local_img) or \
       os.path.getmtime(local_img) < os.path.getmtime(remote_img)):
        if size:
            resize(remote_img, local_img, size[0], size[1])
        else:
            shutil.copy(remote_img, local_img)
