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
    data = open('./data/test.pdf').read()
    self.kw = dict(env=dict(PATH=self.env_path))
    self.pdfgranulator = PDFGranulator(self.tmp_url, data, 'pdf', **self.kw)

  def testGetImageItemList(self):
    """Test if getImageItemList() returns the right images list"""
    image_list = self.pdfgranulator.getImageItemList()
    self.assertEquals([('10000000000000C80000009C38276C51.jpg', ''),
                       ('10000201000000C80000004E7B947D46.png', 'TioLive Logo'),
                       ('10000201000000C80000004E7B947D46.png', ''),
                       # XXX The svg image are stored into odf as svm
                       ('2000004F00004233000013707E7DE37A.svm', 'Python Logo'),
                       ('10000201000000C80000004E7B947D46.png',
                        'Again TioLive Logo')], image_list)

def test_suite():
  return make_suite(TestPDFGranulator)
