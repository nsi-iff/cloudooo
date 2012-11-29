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
from tempfile import mkdtemp, NamedTemporaryFile
from lxml import etree
from glob import glob
import shutil
import os

try:
  import Image
except ImportError:
  from PIL import Image

def get_text(element):
  try:
    txt = element[0].text
  except:
    txt = element.text
  return txt

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
    # XXX - PDF can be protect
    if 'Erro' in stderr:
      return False
    else:
      removeEqualImages(self.grain_directory)
      images = glob("%s/*.*"%self.grain_directory)
      imagesList = getImages(images)
      return imagesList

  def getTableItemList(self):
    """Returns the list of table title"""
    tables = self.getTablesMatrix()
    if tables == False:
      return "PDF Protect or have no Table Item List"
    else:
      table_list = tables.keys()
      return table_list

  def getTable(self, id, format='html'):
    """Returns the table into html format."""
    try:
      table_matrix = self.getTablesMatrix()[id]
      content = '<html><body><h1> %s </h1><table>' % id
      for line in table_matrix:
        content += '<tr>'
        for column in line:
          if not type(column) == list:
            content += '<td> %s </td>' % column
          else:
            content +='<td>'
            for element in column:
              content += '%s </br>' % element
            content += '</td>'
        content +='</tr>'
      content += '</table></body></html>'
      return content
    except:
      return "PDF Protect or have no table with this id"


  def getTablesMatrix(self):
    """Returns the table as a matrix"""
    logger.debug("PDFTableGrainExtract")
    output_url = NamedTemporaryFile(suffix=".xml",dir=self.file.directory_name).name
    command = ["pdftohtml", "-xml",  self.file.getUrl(), output_url]
    stdout, stderr = Popen(command,
                          stdout=PIPE,
                          stderr=PIPE,
                          close_fds=True,
                          env=self.environment).communicate()
    # XXX - PDF can be protect
    if 'Erro' in stderr:
      return False
    else:
      output = etree.fromstring(open(output_url).read())
      row_list = output.xpath('//text')
      name,previous,next = '', '', ''
      tables = {}
      element = []
      line = []
      matrix = []
      i,j,l,m = 0,0,0,0
      old_x_left = 600
      for x in row_list:
        base_line = x.attrib['top']
        base_column = x.attrib['left']
        i += 1
        for y in row_list[i:]:
          if base_line == y.attrib['top']:
            l += 1
            line.append(get_text(y))
            base_column = y.attrib['left']
            row_list.remove(y)
          elif base_column == y.attrib['left']:
            m = l
            if len(element) > 0:
              element.append(get_text(y))
            # In case name of the table is after table
            if len(line) == 0:
              next = get_text(x)
              if next != None and len(next.split(':')) == 2:
                name = next
                next = ''
            elif len(line) > 0:
              element.append(line.pop())
              element.append(get_text(y))
          else:
            if len(element) > 0:
              line.insert(m-1,element)
            l = 0
            element = []
            base_column = 0
            break

        if len(line)>0:
          # In case name of the table is before table
          previous = get_text(x.getprevious())
          if previous != None and len(previous.split(':')) == 2:
            name = previous
            previous = ''
          line.insert(0,get_text(x))
          if len(line) > 1:
            matrix.append(line)
        line = []
        if x.attrib['left'] < old_x_left and len(matrix)>0:
          if len(matrix)>0:
            j += 1
            if name == '':
              name = "Tabela %d" % j
            name += " - pag %s" % x.getparent().attrib['number']
            tables[name]= matrix
          name = ''
          matrix = []
        old_x_left = x.attrib['left']
      return tables


  def trash(self):
    """Remove file from memory"""
    self.file.trash()
