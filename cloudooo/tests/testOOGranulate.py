# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Hugo H. Maia Vieira <hugomaia@tiolive.com>
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

import unittest
from zipfile import ZipFile
from StringIO import StringIO
from lxml import etree
from cloudoooTestCase import cloudoooTestCase, make_suite
from cloudooo.granulate.oogranulate import OOGranulate


class TestOOGranulate(cloudoooTestCase):

  def setUp(self):
    data = open('./data/granulate_test.odt').read()
    self.oogranulate = OOGranulate(data, 'odt')

  def testOdfWithoutContentXml(self):
    """Test if _odfWithoutContentXml() return a ZipFile instance without the
    content.xml file"""
    odf_without_content_xml = self.oogranulate._odfWithoutContentXml('odt')
    self.assertTrue(isinstance(odf_without_content_xml, ZipFile))
    complete_name_list = []
    for item in self.oogranulate.document._zipfile.filelist:
      complete_name_list.append(item.filename)
    for item in odf_without_content_xml.filelist:
      self.assertTrue(item.filename in complete_name_list)
      self.assertTrue(item.filename != 'content.xml')

  def testgetTableItemList(self):
    """Test if getTableItemList() returns the right tables list"""
    data = open('./data/granulate_table_test.odt').read()
    oogranulate = OOGranulate(data, 'odt')
    table_list = [('Developers', ''),
                  ('Prices', 'Table 1: Prices table from Mon Restaurant'),
                  ('SoccerTeams', 'Tabela 2: Soccer Teams')]
    self.assertEquals(table_list, oogranulate.getTableItemList())

  def testGetTableItem(self):
    """Test if getTableItem() returns on odf file with the right table"""
    data = open('./data/granulate_table_test.odt').read()
    oogranulate = OOGranulate(data, 'odt')
    table_data_doc = oogranulate.getTableItem('Developers')
    content_xml_str = ZipFile(StringIO(table_data_doc)).read('content.xml')
    content_xml = etree.fromstring(content_xml_str)
    table_list = content_xml.xpath('//table:table',
                                   namespaces=content_xml.nsmap)
    self.assertEquals(1, len(table_list))
    table = table_list[0]
    name_key = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name'
    self.assertEquals('Developers', table.attrib[name_key])

  def testGetTableItemWithoutSuccess(self):
    """Test if getTableItem() returns None for an non existent table name"""
    data = open('./data/granulate_table_test.odt').read()
    oogranulate = OOGranulate(data, 'odt')
    table_data = oogranulate.getTableItem('NonExistentTable')
    self.assertEquals(table_data, None)

  def testGetTableMatriz(self):
    """Test if getTableMatrix() returns the right matrix"""
    data = open('./data/granulate_table_test.odt').read()
    oogranulate = OOGranulate(data, 'odt')
    matrix = [['Name', 'Phone', 'Email'],
             ['Hugo', '+55 (22) 8888-8888', 'hugomaia@tiolive.com'],
             ['Rafael', '+55 (22) 9999-9999', 'rafael@tiolive.com']]
    self.assertEquals(matrix, oogranulate.getTableMatrix('Developers'))

    matrix = [['Product', 'Price'],
             ['Pizza', 'R$ 25,00'],
             ['Petit Gateau', 'R$ 10,00'],
             ['Feijoada', 'R$ 30,00']]
    self.assertEquals(matrix, oogranulate.getTableMatrix('Prices'))

    self.assertEquals(None, oogranulate.getTableMatrix('Non existent'))


  def testGetColumnItemList(self):
    """Test if getColumnItemList() returns the right table columns list"""
    self.assertRaises(NotImplementedError, self.oogranulate.getColumnItemList,
                                     'file',
                                     'table_id')

  def testGetLineItemList(self):
    """Test if getLineItemList() returns the right table lines list"""
    self.assertRaises(NotImplementedError, self.oogranulate.getLineItemList,
                                     'file',
                                     'table_id')

  def testGetImageItemList(self):
    """Test if getImageItemList() returns the right images list"""
    image_list = self.oogranulate.getImageItemList()
    self.assertEquals([
      ('10000000000000C80000009C38276C51.jpg', ''),
      ('10000201000000C80000004E7B947D46.png', ''),
      ('10000201000000C80000004E7B947D46.png', 'Illustration 1: TioLive Logo'),
      # XXX The svg image are stored into odf as svm
      ('2000004F00004233000013707E7DE37A.svm', 'Figure 1: Python Logo'),
      ('10000201000000C80000004E7B947D46.png',
        'Illustration 2: Again TioLive Logo'),
      ], image_list)

  def testGetImageSuccessfully(self):
    """Test if getImage() returns the right image file successfully"""
    data = open('./data/granulate_test.odt').read()
    zip = ZipFile(StringIO(data))
    image_id = '10000000000000C80000009C38276C51.jpg'
    original_image = zip.read('Pictures/%s' % image_id)
    geted_image = self.oogranulate.getImage(image_id)
    self.assertEquals(original_image, geted_image)

  def testGetImageWithoutSuccess(self):
    """Test if getImage() returns an empty string for not existent id"""
    obtained_image = self.oogranulate.getImage('anything.png')
    self.assertEquals('', obtained_image)

  def testGetParagraphItemList(self):
    """Test if getParagraphItemList() returns the right paragraphs list, with
    the ids always in the same order"""
    for i in range(5):
      data = open('./data/granulate_test.odt').read()
      oogranulate = OOGranulate(data, 'odt')
      paragraph_list = oogranulate.getParagraphItemList()
      self.assertEquals((0, 'P3'), paragraph_list[0])
      self.assertEquals((1, 'P1'), paragraph_list[1])
      self.assertEquals((2, 'P12'), paragraph_list[2])
      self.assertEquals((8, 'P13'), paragraph_list[8])
      self.assertEquals((19, 'Standard'), paragraph_list[19])

  def testGetParagraphItemSuccessfully(self):
    """Test if getParagraphItem() returns the right paragraph"""
    self.assertEquals(('Some images without title', 'P13'),
                      self.oogranulate.getParagraphItem(8))

    big_paragraph = self.oogranulate.getParagraphItem(5)
    self.assertEquals('P8', big_paragraph[1])
    self.assertTrue(big_paragraph[0].startswith(u'A prática cotidiana prova'))
    self.assertTrue(big_paragraph[0].endswith(u'corresponde às necessidades.'))

  def testGetParagraphItemWithoutSuccess(self):
    """Test if getParagraphItem() returns None for not existent id"""
    self.assertEquals(None, self.oogranulate.getParagraphItem(200))

  def testGetChapterItemList(self):
    """Test if getChapterItemList() returns the right chapters list"""
    self.assertRaises(NotImplementedError, self.oogranulate.getChapterItemList,
                                           'file')

  def testGetChapterItem(self):
    """Test if getChapterItem() returns the right chapter"""
    self.assertRaises(NotImplementedError, self.oogranulate.getChapterItem,
                                     'file',
                                     'chapter_id')


def test_suite():
  return make_suite(TestOOGranulate)

if __name__ == "__main__":
  suite = unittest.TestLoader().loadTestsFromTestCase(TestOOGranulate)
  unittest.TextTestRunner(verbosity=2).run(suite)
