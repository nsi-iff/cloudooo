# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009-2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Gabriel M. Monnerat <gabriel@tiolive.com>
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

import mimetypes
from mimetypes import guess_all_extensions, guess_extension
from base64 import encodestring, decodestring
from zope.interface import implements
from interfaces.manager import IManager, IERP5Compatibility
from cloudooo.util import logger
from cloudooo.interfaces.granulate import ITableGranulator
from cloudooo.interfaces.granulate import IImageGranulator
from cloudooo.interfaces.granulate import ITextGranulator
from fnmatch import fnmatch

#XXX Must be removed
from cloudooo.handler.ooo.granulator import OOGranulator
from cloudooo.handler.ooo.mimemapper import mimemapper
from cloudooo.handler.pdf.granulator import PDFGranulator

class HandlerNotFound(Exception):
  pass

def getHandlerClass(source_format, destination_format, mimetype_registry,
                    handler_dict):
  """Select handler according to source_format and destination_format
  """
  source_mimetype = mimetypes.types_map.get('.%s' % source_format, "*")
  destination_mimetype = mimetypes.types_map.get('.%s' % destination_format, "*")
  for pattern in mimetype_registry:
    registry_list = pattern.split()
    if fnmatch(source_mimetype, registry_list[0]) and \
        (fnmatch(destination_mimetype, registry_list[1]) or destination_format is None):
      return handler_dict[registry_list[2]]
  raise HandlerNotFound('No Handler found for %r=>%r' % (source_format,
                                                         destination_format))


class Manager(object):
  """Manipulates requisitons of client and temporary files in file system."""
  implements(IManager, IERP5Compatibility, ITableGranulator, IImageGranulator,
             ITextGranulator)

  def __init__(self, path_tmp_dir, **kw):
    """Need pass the path where the temporary document will be created."""
    self._path_tmp_dir = path_tmp_dir
    self.kw = kw
    self.mimetype_registry = self.kw.pop("mimetype_registry")
    self.handler_dict = self.kw.pop("handler_dict")

  def convertFile(self, file, source_format, destination_format, zip=False,
                  refresh=False):
    """Returns the converted file in the given format.
    Keywords arguments:
      file -- File as string in base64
      source_format -- Format of original file as string
      destination_format -- Target format as string
      zip -- Boolean Attribute. If true, returns the file in the form of a
      zip archive
    """
    self.kw['zip'] = zip
    self.kw['refresh'] = refresh
    handler_class = getHandlerClass(source_format,
                                    destination_format,
                                    self.mimetype_registry,
                                    self.handler_dict)
    handler = handler_class(self._path_tmp_dir,
                            decodestring(file),
                            source_format,
                            **self.kw)
    decode_data = handler.convert(destination_format)
    return encodestring(decode_data)

  def updateFileMetadata(self, file, source_format, metadata_dict):
    """Receives the string of document and a dict with metadatas. The metadata
    is added in document.
    e.g
    self.updateFileMetadata(data = encodestring(data), metadata = \
      {"title":"abc","description":...})
    return encodestring(document_with_metadata)
    """
    handler_class = getHandlerClass(source_format,
                               None,
                               self.mimetype_registry,
                               self.handler_dict)
    handler = handler_class(self._path_tmp_dir,
                            decodestring(file),
                            source_format,
                            **self.kw)
    metadata_dict = dict([(key.capitalize(), value) \
                        for key, value in metadata_dict.iteritems()])
    decode_data = handler.setMetadata(metadata_dict)
    return encodestring(decode_data)

  def getFileMetadataItemList(self, file, source_format, base_document=False):
    """Receives the string of document as encodestring and returns a dict with
    metadatas.
    e.g.
    self.getFileMetadataItemList(data = encodestring(data))
    return {'Title': 'abc','Description': 'comments', 'Data': None}

    If converted_data is True, the ODF of data is added in dictionary.
    e.g
    self.getFileMetadataItemList(data = encodestring(data), True)
    return {'Title': 'abc','Description': 'comments', 'Data': string_ODF}

    Note that all keys of the dictionary have the first word in uppercase.
    """
    handler_class = getHandlerClass(source_format,
                                    None,
                                    self.mimetype_registry,
                                    self.handler_dict)
    handler = handler_class(self._path_tmp_dir,
                            decodestring(file),
                            source_format,
                            **self.kw)
    metadata_dict = handler.getMetadata(base_document)
    metadata_dict['Data'] = encodestring(metadata_dict.get('Data', ''))
    return metadata_dict

  def getAllowedExtensionList(self, request_dict={}):
    """List types which can be generated from given type
    Type can be given as:
      - filename extension
      - document type ('text', 'spreadsheet', 'presentation' or 'drawing')
    e.g
    self.getAllowedMimetypeList(dict(document_type="text"))
    return extension_list
    """
    mimetype = request_dict.get('mimetype')
    extension = request_dict.get('extension')
    document_type = request_dict.get('document_type')
    if mimetype:
      allowed_extension_list = []
      for ext in guess_all_extensions(mimetype):
        ext = ext.replace('.', '')
        extension_list = mimemapper.getAllowedExtensionList(extension=ext,
                                                 document_type=document_type)
        for extension in extension_list:
          if extension not in allowed_extension_list:
            allowed_extension_list.append(extension)
      return allowed_extension_list
    elif extension:
      extension = extension.replace('.', '')
      return mimemapper.getAllowedExtensionList(extension=extension,
                                                 document_type=document_type)
    elif document_type:
      return mimemapper.getAllowedExtensionList(document_type=document_type)
    else:
      return [('', '')]

  def run_convert(self, filename='', data=None, meta=None, extension=None,
                  orig_format=None):
    """Method to support the old API. Wrapper getFileMetadataItemList but
    returns a dict.
    This is a Backwards compatibility provided for ERP5 Project, in order to
    keep compatibility with OpenOffice.org Daemon.
    """
    if not extension:
      extension = filename.split('.')[-1]
    try:
      response_dict = {}
      metadata_dict = self.getFileMetadataItemList(data, extension,
                                                   base_document=True)
      response_dict['meta'] = metadata_dict
      # XXX - Backward compatibility: Previous API expects 'mime' now we
      # use 'MIMEType'
      response_dict['meta']['mime'] = response_dict['meta']['MIMEType']
      response_dict['data'] = response_dict['meta']['Data']
      response_dict['mime'] = response_dict['meta']['MIMEType']
      del response_dict['meta']['Data']
      return (200, response_dict, "")
    except Exception, e:
      import traceback; traceback.print_exc()
      logger.error(e)
      return (402, {}, e.args[0])

  def run_setmetadata(self, filename='', data=None, meta=None,
                      extension=None, orig_format=None):
    """Wrapper updateFileMetadata but returns a dict.
    This is a Backwards compatibility provided for ERP5 Project, in order to
    keep compatibility with OpenOffice.org Daemon.
    """
    if not extension:
      extension = filename.split('.')[-1]
    response_dict = {}
    try:
      response_dict['data'] = self.updateFileMetadata(data, extension, meta)
      return (200, response_dict, '')
    except Exception, e:
      logger.error(e)
      return (402, {}, e.args[0])

  def run_getmetadata(self, filename='', data=None, meta=None,
                      extension=None, orig_format=None):
    """Wrapper for getFileMetadataItemList.
    This is a Backwards compatibility provided for ERP5 Project, in order to
    keep compatibility with OpenOffice.org Daemon.
    """
    if not extension:
      extension = filename.split('.')[-1]
    response_dict = {}
    try:
      response_dict['meta'] = self.getFileMetadataItemList(data, extension)
      # XXX - Backward compatibility: Previous API expects 'title' now
      # we use 'Title'"
      response_dict['meta']['title'] = response_dict['meta']['Title']
      return (200, response_dict, '')
    except Exception, e:
      logger.error(e)
      return (402, {}, e.args[0])

  def run_generate(self, filename='', data=None, meta=None, extension=None,
                   orig_format=''):
    """Wrapper convertFile but returns a dict which includes mimetype.
    This is a Backwards compatibility provided for ERP5 Project, in order
    to keep compatibility with OpenOffice.org Daemon.
    """
    # calculate original extension required by convertFile from
    # given content_type (orig_format)
    original_extension = guess_extension(orig_format).strip('.')
    # XXX - ugly way to remove "/" and "."
    orig_format = orig_format.split('.')[-1]
    orig_format = orig_format.split('/')[-1]
    if "htm" in extension:
      zip = True
    else:
      zip = False
    try:
      response_dict = {}
      # XXX - use html format instead of xhtml
      if orig_format in ("presentation",
                         "graphics",
                         "spreadsheet",
                         'text') and extension == "xhtml":
        extension = 'html'
      response_dict['data'] = self.convertFile(data,
                                               original_extension,
                                               extension,
                                               zip)
      # FIXME: Fast solution to obtain the html or pdf mimetypes
      if zip:
        response_dict['mime'] = "application/zip"
      elif extension == 'xhtml':
        response_dict['mime'] = "text/html"
      else:
        response_dict['mime'] = mimetypes.types_map.get('.%s' % extension)
      return (200, response_dict, "")
    except Exception, e:
      logger.error(e)
      return (402, response_dict, str(e))

  def getAllowedTargetItemList(self, content_type):
    """Wrapper getAllowedExtensionList but returns a dict.
    This is a Backwards compatibility provided for ERP5 Project, in order to
    keep compatibility with OpenOffice.org Daemon.
    """
    response_dict = {}
    try:
      extension_list = self.getAllowedExtensionList({"mimetype": content_type})
      response_dict['response_data'] = extension_list
      return (200, response_dict, '')
    except Exception, e:
      logger.error(e)
      return (402, {}, e.args[0])


  def granulateFile(self, data, source_format="odt"):
    """This function allows BD NSI's project to completely granulate 
    document file"""
    if source_format.lower() == "pdf":
      pdfgranulator = PDFGranulator(self._path_tmp_dir, decodestring(data), 'pdf',
                                **self.kw)
      table_list = pdfgranulator.getTableItemList()
      grains = []
      if table_list != 'PDF Protect or have no Table Item List':
        tables = []
        for item in table_list:
          table = pdfgranulator.getTable(item)
          tables.append(table)
        grains = map(encodestring, tables)
      images = pdfgranulator.getImageItemList()
      if images != False:
        # XXX - encodestring cant convert list
        grains += map(encodestring, str(images))

      # XXX - if has no grains
      if grains == []:
        return "This PDF is protect or has no grains"
      return grains
    
    else:
      try:
        document = self._getOOGranulator(data, source_format)
        table_list = document.getTableItemList()
        tables = []
        for table in table_list:
          tables.append(document.getTable(table[0], 'odt'))
        grains = tables
        image_list = document.getImageItemList()
        images = []
        for image in image_list:
          images.append(document.getImage(image[0]))
        grains += image
        return map(encodestring,grains)
      except:
        raise NotImplementedError


  # XXX - This should be rewritten for all granulators
  def _getOOGranulator(self, data, source_format="odt"):
    """Returns an instance of the handler OOGranulator after convert the
    data to 'odt'"""
    GRANULATABLE_FORMAT_LIST = ("odt",)
    if source_format not in GRANULATABLE_FORMAT_LIST:
      data = self.convertFile(data, source_format,
                    GRANULATABLE_FORMAT_LIST[0], zip=False)
    return OOGranulator(decodestring(data), GRANULATABLE_FORMAT_LIST[0])

  def getTableItemList(self, data, source_format="odt"):
    """Returns the list of table IDs in the form of (id, title)."""
    document = self._getOOGranulator(data, source_format)
    return document.getTableItemList()

  def getTable(self, data, id, source_format="odt"):
    """Returns the table into a new 'format' file."""
    document = self._getOOGranulator(data, source_format)
    #the file will be convert; so, the source_format will be always 'odt'
    return encodestring(document.getTable(id, 'odt'))

  def getColumnItemList(self, data, table_id, source_format):
    """Return the list of columns in the form of (id, title)."""
    document = self._getOOGranulator(data, source_format)
    return document.getColumnItemList(table_id)

  def getLineItemList(self, data, table_id, source_format):
    """Returns the lines of a given table as (key, value) pairs."""
    document = self._getOOGranulator(data, source_format)
    return document.getLineItemList(table_id)

  def getImageItemList(self, data, source_format):
    """Return the list of images in the form of (id, title)."""
    data = self.convertFile(data, source_format, 'odt', zip=False)
    document = self._getOOGranulator(data, source_format)
    return document.getImageItemList()

  def getImage(self, data, image_id, source_format, format=None,
               resolution=None, **kw):
    """Return the given image."""
    document = self._getOOGranulator(data, source_format)
    return encodestring(document.getImage(image_id, format, resolution, **kw))

  def getParagraphItemList(self, data, source_format):
    """Returns the list of paragraphs in the form of (id, class) where class
       may have special meaning to define TOC/TOI."""
    document = self._getOOGranulator(data, source_format)
    return document.getParagraphItemList()

  def getParagraph(self, data, paragraph_id, source_format):
    """Returns the paragraph in the form of (text, class)."""
    document = self._getOOGranulator(data, source_format)
    return document.getParagraph(paragraph_id)

  def getChapterItemList(self, data, source_format):
    """Returns the list of chapters in the form of (id, level)."""
    document = self._getOOGranulator(data, source_format)
    return document.getChapterItemList()

  def getChapterItem(self, chapter_id, data, source_format):
    """Return the chapter in the form of (title, level)."""
    document = self._getOOGranulator(data, source_format)
    return document.getChapterItem(chapter_id)
