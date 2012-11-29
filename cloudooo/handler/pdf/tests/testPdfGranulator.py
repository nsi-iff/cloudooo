# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
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

from cloudooo.tests.handlerTestCase import HandlerTestCase, make_suite
from cloudooo.handler.pdf.granulator import PDFGranulator


class TestPDFGranulator(HandlerTestCase):

  def afterSetUp(self):
    self.kw = dict(env=dict(PATH=self.env_path))

  def testGetImageItemList(self):
    """Test if getImageItemList() returns the right images list"""
    data = open('./data/test.pdf').read()
    pdfgranulator = PDFGranulator(self.tmp_url, data, 'pdf', **self.kw)
    image_list = pdfgranulator.getImageItemList()
    self.assertEquals(image_list[0][0], '001-pag001.png')
    self.assertEquals(image_list[-1][0], '012-pag004.jpg')
    self.assertEquals(len(image_list), 12)

  def testGetTable(self):
    """Test if getTable() returns table by id"""
    data = open('./data/granulate_test.pdf').read()
    pdfgranulator = PDFGranulator(self.tmp_url, data, 'pdf', **self.kw)
    table = pdfgranulator.getTable('Tabela 1 - pag 1')
    self.assertEqual(table, '<html><body><h1> Tabela 1 - pag 1 </h1><table>'+
    '<tr><td> Name </td><td> Phone </td><td> Email </td></tr>'+
    '<tr><td> Hugo </td><td> +55 (22) 8888-8888 </td><td> hugomaia@tiolive.com </td></tr>'+
    '<tr><td> Rafael </td><td>+55 (22) 9999-9999 </br>+55 (22) 9999-9999 '+
    '</br>+55 (22) 9999-9999 </br></td><td> rafael@tiolive.com </td></tr></table></body></html>')

  def testGetTableItemList(self):
    """Test if getTableItemList() returns list of tables' id"""
    data = open('./data/granulate_test.pdf').read()
    pdfgranulator = PDFGranulator(self.tmp_url, data, 'pdf', **self.kw)
    table_list = pdfgranulator.getTableItemList()
    self.assertEqual(table_list, ['Tabela 2: Soccer Teams - pag 2', 'Tabela 1 - pag 1', 'Table 1: Prices table from Mon Restaurant - pag 1'])

  def testGetTablesMatrix(self):
    """Test if getTablesMatrix() returns matrix with all tables"""
    data = open('./data/granulate_test.pdf').read()
    pdfgranulator = PDFGranulator(self.tmp_url, data, 'pdf', **self.kw)
    tables_matrix = pdfgranulator.getTablesMatrix()
    self.assertEqual(tables_matrix,
    {'Tabela 2: Soccer Teams - pag 2': [
        ['Name', 'Country'], ['Goytacaz', 'Brazil'], ['PSG', 'France'], ['Chelsea', 'England '], ['Barcelona', 'Spain']], 
      'Tabela 1 - pag 1': [
        ['Name', 'Phone', 'Email'], 
        ['Hugo', '+55 (22) 8888-8888', 'hugomaia@tiolive.com'], 
        ['Rafael', ['+55 (22) 9999-9999', '+55 (22) 9999-9999', '+55 (22) 9999-9999'], 'rafael@tiolive.com']], 
      'Table 1: Prices table from Mon Restaurant - pag 1': [
        ['Product', 'Price'], ['Pizza', 'R$ 25,00'], ['Petit Gateau', 'R$ 10,00'], ['Feijoada', 'R$ 30,00']]})

  def testGetTablesImagesFromProtectPDF(self):
    """Test if protect pdf returns False when try to extract tables and images"""
    data = open('./data/test_protect.pdf').read()
    pdfgranulator = PDFGranulator(self.tmp_url, data, 'pdf', **self.kw)
    tables_matrix = pdfgranulator.getTablesMatrix()
    image_list = pdfgranulator.getImageItemList()
    self.assertEqual(tables_matrix, False)
    self.assertEqual(image_list, False)


def test_suite():
  return make_suite(TestPDFGranulator)
