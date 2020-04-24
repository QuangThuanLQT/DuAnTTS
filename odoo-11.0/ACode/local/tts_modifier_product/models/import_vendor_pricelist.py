# -*- coding: utf-8 -*-

from odoo import models, fields, api
import StringIO
import xlsxwriter
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook
from odoo.exceptions import UserError, ValidationError


class import_vendor_pricelist(models.Model):
    _name = 'import.vendor.pricelist'

    data_import = fields.Binary()


    def import_csv(self):
        data = base64.b64decode(self.data_import)
        wb = open_workbook(file_contents=data)
        sheet = wb.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            if row_no > 0:
                row = (map(lambda row: isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value),
                           sheet.row(row_no)))
                if not row[0] or  not row[1] or not row[2] or not row[3] or not row[4] or not row[5]:
                    continue
                else:
                    partner_id = self.env['res.partner'].search([('name', '=', row[0]), ('supplier', '=', True)], limit=1)
                    if not partner_id:
                        partner_id = self.env['res.partner'].create({
                            'name': row[0],
                            'supplier': True
                        })
                    if row[1]:
                        product_tmpl_id = self.env['product.template'].search([('default_code', '=', row[1])], limit=1)
                        if product_tmpl_id and partner_id:
                            vendor_pricelist_id = self.env['product.supplierinfo'].search([('name', '=', partner_id.id), ('product_tmpl_id', '=', product_tmpl_id.id)])
                            if not vendor_pricelist_id:
                                vendor_pricelist_id = self.env['product.supplierinfo'].create({
                                    'name': partner_id.id,
                                    'product_tmpl_id': product_tmpl_id.id
                                })
                                product_id = self.env['product.product'].search([('default_code', '=', row[2])], limit=1)
                                vendor_pricelist_line = self.env['product.variants.line'].create({
                                    'line_id': vendor_pricelist_id.id,
                                    'product_id': product_id.id,
                                    'product_name': product_id.name,
                                    'price': row[12],
                                    'monthly_discount': row[11],
                                    'attribute_value_ids': [(6, 0, product_id.attribute_value_ids.ids)]
                                })
                            else:
                                product_id = self.env['product.product'].search([('default_code', '=', row[2])],
                                                                                limit=1)
                                vendor_pricelist_line = self.env['product.variants.line'].create({
                                    'line_id': vendor_pricelist_id.id,
                                    'product_id': product_id.id,
                                    'product_name': product_id.name,
                                    'price': row[12],
                                    'monthly_discount': row[11],
                                    'attribute_value_ids': [(6, 0, product_id.attribute_value_ids.ids)]
                                })
                            print 'Done line %s' % row_no