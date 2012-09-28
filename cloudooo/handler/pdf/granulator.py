##############################################################################
#
# Copyright (c) 2009-2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Priscila Manhaes <priscila@tiolive.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from cloudooo.file import File
from cloudooo.util import logger
from cloudooo.handler.imagemagick.handler import Handler
from subprocess import Popen, PIPE
from tempfile import mkdtemp
from glob import glob
import shutil
import os

try:
  import Image
except ImportError:
  from PIL import Image

def removeEqualImages(path):
  """This function verify if images are equals and remove it from path
  It was based on images histogram of nsi.granulate"""
  imagesList = []
  images = glob("%s/*.*"%path)
  for image in images:
    if image.split(".")[-1] == 'html':
      os.remove(os.path.join(path,image))
      continue
    try:
      img = Image.open(image)
      imagesList.append({'filename':image.split("/")[-1],'objImage':img})
    except IOError:
      pass
  i = 0
  imagesList.sort()
  for imgDict in imagesList:
    i += 1
    for imgDict2 in imagesList[i:]:
      if imgDict['objImage'].histogram() == imgDict2['objImage'].histogram():
        imagesList.remove(imgDict2)
        os.remove(os.path.join(path,imgDict2['filename']))

def getImages(images):
  """This function verify if there is ppm and pbm and converts it to png
  before return the list of images in document"""
  imagesList = []
  images.sort()
  id = 0
  for image in images:
    id += 1
    page = int(image.split('/-')[-1].split('_')[0])
    extension = image.split(".")[-1]
    title = image.split('-')[0] + "%.3d-pag%.3d." % (id,page) + extension
    if extension in ('ppm', 'pbm',):
      img = Handler("/".join(image.split("/")[:-1]), open(image).read(), image.split(".")[-1])
      new_image = image.split(".")[0]+".png"
      content = img.convert("png")
      open(new_image,'w').write(content)
      img = open(new_image).read()
      imagesList.append([title.split("/")[-1], img])
    else:
      imagesList.append([title.split("/")[-1], open(image).read()])
  return imagesList

class PDFGranulator(object):

  def __init__(self, base_folder_url, data, source_format, **kw):
    self.file = File(base_folder_url, data, source_format)
    self.environment = kw.get("env", {})
    self.grain_directory = mkdtemp(dir=self.file.directory_name)

  # XXX - It should have another name for returning all images
  def getImageItemList(self):
    logger.debug("PDFImageGrainExtract")
    command = ["pdftohtml", self.file.getUrl(), "%s/"%self.grain_directory]
    stdout, stderr = Popen(command,
                          stdout=PIPE,
                          stderr=PIPE,
                          close_fds=True,
                          env=self.environment).communicate()
    removeEqualImages(self.grain_directory)
    images = glob("%s/*.*"%self.grain_directory)
    imagesList = getImages(images)
    self.file.trash()
    return imagesList
