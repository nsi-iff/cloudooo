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

try:
  import Image
except ImportError:
  from PIL import Image

def removeEqualImages(images):
  """This function verify if images are equals and remove it from same path
  and it was based on images histogram of nsi.granulate"""
  imagesList = []
  for image in images:
    try:
      img = Image.open(image)
      imageList.append({'filename':image.split("/")[-1],'objImage':img})
    except IOError:
      pass
    i=0
    for imgDict in imageList:
      i+=1
      for imgDict2 in imageList[i:]:
        if imgDict['objImage'].histogram() == imgDict2.histogram()
          os.remove(os.path.join(path,imgDict2['filename']))

def getImages(images):
  """This function verify if there is ppm and pbm and converts it to png
  before return the list of images in document"""
  imageList = []
  for image in images:
    extension = image.split(".")[-1]
    if extension in ('ppm', 'pbm',):
      img = Handler("/".join(image.split("/")[:-1]), open(image).read(), image.split(".")[-1])
      new_image = image.split("/")[-1].split(".")[0]+"png"
      img = open(new_image,'w').write(img.convert("png"))
      imageList.append([new_image.split("/")[-1], img])
      img.close()
      os.remove(image, img)
  return imageList

class PDFGranulator(object):

  def __init__(self, base_folder_url, data, source_format, **kw):
    self.file = File(base_folder_url, data, source_format)
    self.environment = kw.get("env", {})
    self.grain_directory = mkdtemp(dir="%s/%s"%(base_folder_url, 'grains'))

  # XXX - It should have another name for returning all images
  def getImageItemList(self):
    logger.debug("PDFImageGrainExtract")
    command = ["pdfimage", "-j", self.file.getUrl(), self.grain_directory]
    stdout, stderr = Popen(command,
                          stdout=PIPE,
                          stderr=PIPE,
                          close_fds=True,
                          env=self.environment).communicate()
    removeEqualImages(self.grain_directory)
    imageList = convertPPMImages(self.grain_directory)
    return imageList

