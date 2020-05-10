# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64
import StringIO
import os
import tempfile
import shutil
import xlsxwriter
import json

from xlrd import open_workbook
import os


class import_purchase_order(models.TransientModel):
    _name = 'import.sale.group'

    import_data = fields.Binary(string="File Import")
    check_update_customer = fields.Boolean("Cập nhật theo khách hàng")

    @api.multi
    def import_xls(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)
                list_customer = []
                count = 0
                # product_ids = self.env['product.template'].search([('standard_price', '=', 0)])
                # for product_id in product_ids:
                #     product_id.standard_price = 1

                for row_no in range(sheet.nrows):

                    # TODO import group product sale
                    if row_no == 0:
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                        for no in range(2, len(line)):
                            list_customer.append(line[no].strip())
                    if row_no >= 1:
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                        group_id = self.env['product.group.sale'].search([('name','=',line[0].strip())])
                        if len(group_id) > 1:
                            group_ids = group_id - group_id[0]
                            group_id = group_id[0]
                            group_id.merge_sale_group(group_ids)
                        if group_id:
                            price_type = 'list_price' if line[1] != 'CPnewest' else 'standard_price'
                            if group_id.price_type != price_type:
                                group_id.price_type = price_type
                        if not group_id:
                            group_id = self.env['product.group.sale'].create({
                                'name' : line[0].strip(),
                                'price_type' : 'list_price' if line[1] != 'CPnewest' else 'standard_price'
                            })
                        if not record.check_update_customer:
                            if group_id.group_line_ids:
                                group_id.group_line_ids.unlink()
                            for no in range(0, len(line) - 2):
                                if float(line[no+2]) != 0:
                                    line_data = {
                                        'partner_name' : list_customer[no],
                                        'discount'     : float(line[no+2])
                                    }
                                    group_line = group_id.group_line_ids.new(line_data)
                                    group_id.group_line_ids += group_line
                        else:
                            for no in range(0, len(line) - 2):
                                group_line = self.env['product.group.sale.line'].search(
                                    [('product_group_sale_id', '=', group_id.id),
                                     ('partner_name', '=', list_customer[no])])
                                if group_line:
                                    if group_line.discount != float(line[no+2]):
                                        group_line.discount = float(line[no+2])
                                else:
                                    if float(line[no + 2]) != 0:
                                        line_data = {
                                            'partner_name': list_customer[no],
                                            'discount': float(line[no + 2])
                                        }
                                        group_line = group_id.group_line_ids.new(line_data)
                                        group_id.group_line_ids += group_line
            else:
                group_sale_ids = self.env['product.group.sale'].search([])
                for group_sale_id in group_sale_ids:
                    group_sale_id.name = group_sale_id.name.strip()
                    for line in group_sale_id.group_line_ids:
                        line.partner_name = line.partner_name.strip()

                    #TODO update cost sp
                #     if row_no > 0:
                #         line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                #                     sheet.row(row_no)))
                #         product_id = self.env['product.template'].search([('default_code','=',line[0])])
                #         if product_id:
                #             product_id.standard_price = float(line[2]) or 1
                #             count += 1
                #         else:
                #             product_id = self.env['product.template'].search([('barcode', '=', line[1])])
                #             if product_id:
                #                 product_id.standard_price = float(line[2]) or 1
                #                 count += 1
                #             else:
                #                 print str(row_no+1) + "---------" + str(line[0])
                # print "-----------------" + str(count)