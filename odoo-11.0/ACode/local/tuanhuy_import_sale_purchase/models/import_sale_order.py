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


class import_sale_order(models.TransientModel):
    _name = 'import.sale.order'

    import_data = fields.Binary(string="File Import")
    check_import = fields.Boolean('Allow import',default=False)

    @api.multi
    def check_import_file(self):
        for record in self:
            data = base64.b64decode(record.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)

            data_list = {
                'product_not_find' : [],
                'price_not_sync'   : [],
                'customer_not_find': [],
            }

            for row_no in range(sheet.nrows):
                if row_no >= 1:
                    line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))

                    product_id = self.env['product.product'].search([('default_code', '=', line[3])], limit=1)
                    if not product_id:
                        data_list['product_not_find'].append({
                            'line'  : row_no +1 ,
                            'default_code': line[3],
                        })
                    else:
                        if product_id.list_price != float(line[5]) and product_id.list_price not in [0.0,1.0]:
                            data_list['price_not_sync'].append({
                                'line': row_no + 1,
                                'default_code': line[3],
                            })
                    partner_id = self.env['res.partner'].search([('name', '=', line[2]), ('customer', '=', True)], limit=1)
                    if not partner_id:
                        data_list['customer_not_find'].append({
                            'line': row_no + 1,
                            'customer_name': line[2],
                        })

            return {
                'name': 'Import Warning Order',
                'type': 'ir.actions.act_window',
                'res_model': 'import.warning.order',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'data': data_list,
                    'import_data': record.import_data,
                    'name_action': "import.sale.order",
                    'name_model': "import.sale.order",
                }
            }

    @api.model
    def default_get(self, fields):
        res = super(import_sale_order, self).default_get(fields)
        if 'import_data' in self._context:
            res['import_data'] = self._context.get('import_data')
        return res



    @api.multi
    def import_xls(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)

                so_chung_tu = False
                sale_order = False
                count_order = 0
                count_order_line = 0

                for row_no in range(sheet.nrows):
                    if row_no >= 1:
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),sheet.row(row_no)))
                        partner_id = self.env['res.partner'].search([('name', '=', line[2]), ('customer', '=', True)],
                                                                    limit=1)
                        if not partner_id:
                            if not record.check_import:
                                raise UserError(_('Please check file first'))
                            else:
                                self.env['res.partner'].create({
                                    'name': line[2],
                                    'customer': True
                                })
                        product_id = self.env['product.product'].search([('default_code', '=', line[3])], limit=1)
                        if not record.check_import:
                            if not product_id:
                                raise UserError(_('Please check file first'))
                            else:
                                if product_id.list_price != float(line[5]) and product_id.list_price not in [0.0, 1.0]:
                                    raise UserError(_('Please check file first'))
                        else:
                            if not product_id:
                                continue
                        if float(line[9]) != 0:
                            continue
                    if row_no == 1:
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                        if line[0]:
                            so_chung_tu = line[1]
                            date_order = datetime.utcfromtimestamp((float(line[0]) - 25569) * 86400.0)
                            partner_id = self.env['res.partner'].search([('name','=',line[2]),('customer','=',True)],limit=1)
                            product_id = self.env['product.product'].search([('default_code','=',line[3])],limit=1)
                            product_uom_quantity = int(float(line[4]))
                            price_discount = float(line[8])
                            discount = float(line[7])*100
                            sale_order = self.env['sale.order'].create({
                                'partner_id' : partner_id.id,
                                'partner_invoice_id': partner_id.id,
                                'partner_shipping_id': partner_id.id,
                                'origin' : so_chung_tu,
                                'date_order' : date_order,
                            })
                            count_order += 1
                            line_data = {
                                'product_id': product_id.id,
                                'product_uom': product_id.uom_id.id,
                                'discount': discount,
                            }
                            count_order_line += 1
                            sale_order_line = sale_order.order_line.new(line_data)
                            sale_order_line.product_id_change()
                            tax = []
                            if line[6]:
                                tax = self.env['account.tax'].search([('amount', '=',int(float(line[6])*100)),('type_tax_use','=','sale')], limit=1).ids
                                if not tax:
                                    tax = self.env['account.tax'].search(
                                        [('amount', '=', 0),('type_tax_use','=','sale')],
                                        limit=1).ids
                            if tax:
                                sale_order_line.tax_id = [(6, 0, tax)]
                                if int(float(line[6]) * 100) in [0, 5, 10]:
                                    sale_order_line.tax_sub = int(float(line[6]) * 100)
                                else:
                                    sale_order_line.tax_sub = 0
                            sale_order_line.product_qty = product_uom_quantity
                            sale_order_line.product_uom_qty = product_uom_quantity
                            sale_order_line.price_discount = price_discount
                            sale_order_line.price_unit = price_discount*100/(100-discount)
                            sale_order.order_line += sale_order_line
                    if row_no > 1 :
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),sheet.row(row_no)))
                        print "-------------------------" + str(row_no + 1)
                        if line[0]:
                            if line[1] == so_chung_tu:
                                product_id = self.env['product.product'].search([('default_code', '=', line[3])],limit=1)
                                product_uom_quantity = int(float(line[4]))
                                price_discount = float(line[8])
                                discount = float(line[7]) * 100
                                line_data = {
                                    'product_id': product_id.id,
                                    'product_uom': product_id.uom_id.id,
                                    'discount' : discount,
                                }
                                count_order_line += 1
                                sale_order_line = sale_order.order_line.new(line_data)
                                sale_order_line.product_id_change()
                                tax = []
                                if line[6]:
                                    tax = self.env['account.tax'].search([('amount', '=', int(float(line[6])*100)),('type_tax_use','=','sale')],
                                                                         limit=1).ids
                                    if not tax:
                                        tax = self.env['account.tax'].search(
                                            [('amount', '=', 0),('type_tax_use','=','sale')],
                                            limit=1).ids
                                if tax:
                                    sale_order_line.tax_id = [(6, 0, tax)]
                                    if int(float(line[6]) * 100) in [0, 5, 10]:
                                        sale_order_line.tax_sub = int(float(line[6]) * 100)
                                    else:
                                        sale_order_line.tax_sub = 0
                                sale_order_line.product_uom_qty = product_uom_quantity
                                sale_order_line.product_qty = product_uom_quantity
                                sale_order_line.price_discount = price_discount
                                sale_order_line.price_unit = price_discount*100/(100-discount)
                                sale_order.order_line += sale_order_line
                            if line[1] != so_chung_tu:
                                so_chung_tu = line[1]
                                date_order = datetime.utcfromtimestamp((float(line[0]) - 25569) * 86400.0)
                                partner_id = self.env['res.partner'].search([('name', '=', line[2]),('customer','=',True)],limit=1)
                                product_id = self.env['product.product'].search([('default_code', '=', line[3])],limit=1)
                                product_uom_quantity = int(float(line[4]))
                                price_discount = float(line[8])
                                discount = float(line[7]) * 100
                                sale_order = self.env['sale.order'].create({
                                    'partner_id': partner_id.id,
                                    'partner_invoice_id': partner_id.id,
                                    'partner_shipping_id': partner_id.id,
                                    'origin': so_chung_tu,
                                    'date_order' : date_order,
                                })
                                count_order += 1
                                line_data = {
                                    'product_id': product_id.id,
                                    'product_uom': product_id.uom_id.id,
                                    'discount': discount,
                                }
                                count_order_line += 1
                                sale_order_line = sale_order.order_line.new(line_data)
                                sale_order_line.product_id_change()
                                tax = []
                                if line[6]:
                                    tax = self.env['account.tax'].search([('amount', '=', int(float(line[6])*100)),('type_tax_use','=','sale')],
                                                                         limit=1).ids
                                    if not tax:
                                        tax = self.env['account.tax'].search(
                                            [('amount', '=', 0),('type_tax_use','=','sale')],
                                            limit=1).ids
                                if tax:
                                    sale_order_line.tax_id = [(6, 0, tax)]
                                    if int(float(line[6]) * 100) in [0, 5, 10]:
                                        sale_order_line.tax_sub = int(float(line[6]) * 100)
                                    else:
                                        sale_order_line.tax_sub = 0
                                sale_order_line.product_uom_qty = product_uom_quantity
                                sale_order_line.product_qty = product_uom_quantity
                                sale_order_line.price_discount = price_discount
                                sale_order_line.price_unit = price_discount*100/(100-discount)
                                sale_order.order_line += sale_order_line

                print count_order
                print count_order_line
