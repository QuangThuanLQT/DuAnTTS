# -*- coding:utf-8 -*-
from odoo import models, api
import base64
import xlrd
import datetime
import logging
import xlwt
from cStringIO import StringIO
import re
import os


# class feosco_excel(models.Model):
#     _file_name = os.getcwd()
#
#     _name = "feosco.excel"
#     _auto = False
#
#     _logger = logging.getLogger(_name)
#
#     @api.model
#     def import_data(self, pathBinaryExcelFile):  # file: binary data
#         """
#         file: this binary file
#         """
#
#         self._logger.info('===> BEGIN: act_generation_data()')
#         dataDictReturn = {}
#         self._logger.info('...reading excel from local path...%s' % pathBinaryExcelFile)
#         workbook = xlrd.open_workbook(pathBinaryExcelFile)
#         try:
#
#             for sheet_name in workbook.sheet_names():
#                 worksheet = workbook.sheet_by_name(sheet_name)
#                 total_rows = worksheet.nrows
#                 current_row = 0
#                 start_date_index = -1
#                 end_date_index = -1
#                 result = []
#
#                 while current_row < total_rows:
#                     row_data = worksheet.row_values(current_row)
#                     if current_row == 0:
#                         try:
#                             pass
#                         except ValueError:
#                             start_date_index = -1
#                             end_date_index = -1
#                     else:
#                         if start_date_index >= 0:
#                             from_date = datetime(*xlrd.xldate_as_tuple(row_data[start_date_index], workbook.datemode))
#                             row_data[start_date_index] = from_date
#                         if end_date_index >= 0:
#                             to_date = datetime(*xlrd.xldate_as_tuple(row_data[end_date_index], workbook.datemode))
#                             row_data[end_date_index] = to_date
#                     result.append(row_data)
#                     current_row += 1
#                 dataDictReturn[sheet_name] = result
#
#                 except Exception, e:
#             self._logger.error('---> Error %s' % e)
#         finally:
#             self._logger.info('===> END: act_generation_data()')
#             return dataDictReturn
#
#     @api.model
#     def export_data(self, label, list_tupple_data):
#         """
#
#          - label: Label for file excel example: Name, Code, Addres....etc
#          - list_tuple_data: list tuple data example: [('Alex Job', '123 Hoang Van Thu street', )......etc..]
#
#         """
#         self._logger.info('===> BEGIN: export_data()')
#         self._logger.info('label push me: %s' % label)
#         self._logger.info(list_tupple_data)
#         self._logger.info('sum row push me: %s' % len(list_tupple_data))
#         workbook = xlwt.Workbook()
#         worksheet = workbook.add_sheet('Sheet 1')
#
#         for i, fieldname in enumerate(label):
#             worksheet.write(0, i, fieldname)
#             worksheet.col(i).width = 8000  # around 220 pixels
#
#         style = xlwt.easyxf('align: wrap yes')
#         for row_index, row in enumerate(list_tupple_data):
#             for cell_index, cell_value in enumerate(row):
#                 if isinstance(cell_value, basestring):
#                     cell_value = re.sub("\r", " ", cell_value)
#                 if cell_value is False: cell_value = None
#                 worksheet.write(row_index + 1, cell_index, cell_value, style)
#
#         fp = StringIO()
#         workbook.save(fp)
#         fp.seek(0)
#         data = fp.read()
#         fp.close()
#         self._logger.info('===> END: export_data()')
#         return base64.encodestring(data)
