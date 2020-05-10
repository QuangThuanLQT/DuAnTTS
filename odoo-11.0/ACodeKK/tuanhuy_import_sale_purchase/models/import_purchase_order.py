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
    _name = 'import.purchase.order'

    import_data = fields.Binary(string="File Import")
    check_import = fields.Boolean('Allow import',default=False)

    @api.multi
    def check_import_file(self):
        for record in self:
            data = base64.b64decode(record.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)

            data_list = {
                'product_not_find': [],
                'price_not_sync': [],
                'customer_not_find' : [],
            }

            for row_no in range(sheet.nrows):
                if row_no >= 1:
                    line = (
                    map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))

                    product_id = self.env['product.product'].search([('default_code', '=', line[5])], limit=1)
                    if not product_id:
                        data_list['product_not_find'].append({
                            'line': row_no + 1,
                            'default_code': line[5],
                        })

                    partner_id = self.env['res.partner'].search([('name', '=', line[4]), ('supplier', '=', True)],
                                                                limit=1)
                    if not partner_id:
                        data_list['customer_not_find'].append({
                            'line': row_no + 1,
                            'customer_name': line[4],
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
                    'import_data' : record.import_data,
                    'name_action' : "import.purchase.order",
                    'name_model'  : "import.purchase.order",
                }
            }

    @api.model
    def default_get(self, fields):
        res = super(import_purchase_order, self).default_get(fields)
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
                list_not_import = []


                for row_no in range(sheet.nrows):
                    if row_no >= 1:
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),sheet.row(row_no)))
                        partner_id = self.env['res.partner'].search([('name', '=', line[4]), ('supplier', '=', True)],
                                                                    limit=1)
                        if not partner_id:
                            if record.check_import:
                                self.env['res.partner'].create({
                                    'name' : line[4],
                                    'customer' : False,
                                    'supplier': True,
                                })
                            else:
                                raise UserError(_('Please check file first'))

                        product_id = self.env['product.product'].search([('default_code', '=', line[5])], limit=1)
                        if not product_id:
                            if record.check_import:
                                continue
                            else:
                                raise UserError(_('Please check file first'))
                        if int(float(line[11])) != 0:
                            continue
                    if row_no == 1:
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                        if line[0]:
                            so_chung_tu = line[1]
                            date_order = datetime.utcfromtimestamp((float(line[0]) - 25569) * 86400.0)
                            date_planned = datetime.utcfromtimestamp((float(line[0]) - 25569) * 86400.0)
                            invoice_date_real = False
                            if line[2]:
                                invoice_date_real = datetime.utcfromtimestamp((float(line[2]) - 25569) * 86400.0) or False
                            invoice_number_real = line[3] or False
                            partner_id = self.env['res.partner'].search([('name','=',line[4]),('supplier','=',True)],limit=1)
                            product_id = self.env['product.product'].search([('default_code','=',line[5])],limit=1)
                            product_uom_quantity = int(float(line[6]))
                            price_discount = float(line[10])
                            discount = float(line[9]) * 100
                            sale_order = self.env['purchase.order'].create({
                                'partner_id' : partner_id.id,
                                'notes' : so_chung_tu,
                                'date_order' : date_order,
                                'date_planned': date_planned,
                                'invoice_date_real' : invoice_date_real,
                                'invoice_number_real' : invoice_number_real,
                            })
                            count_order += 1
                            line_data = {
                                'product_id': product_id.id,
                                'product_uom': product_id.uom_id.id,
                                'discount': discount,
                            }
                            count_order_line += 1
                            purchase_order_line = sale_order.order_line.new(line_data)
                            purchase_order_line.onchange_product_id()
                            purchase_order_line.price_discount = price_discount
                            purchase_order_line.price_unit = price_discount*100/(100-discount)
                            purchase_order_line.product_qty = product_uom_quantity
                            tax = []
                            if line[8]:
                                number_tax = int(float(line[8])*100)
                                tax = self.env['account.tax'].search([('amount', '=', number_tax),('type_tax_use','=','purchase')], limit=1).ids
                                if not tax:
                                    tax = self.env['account.tax'].search([('amount', '=', 0),('type_tax_use','=','purchase')], limit=1).ids
                            if tax:
                                purchase_order_line.taxes_id = [(6, 0, tax)]
                                if int(float(line[8]) * 100) in [0, 5, 10]:
                                    purchase_order_line.tax_sub = int(float(line[8]) * 100)
                                else:
                                    purchase_order_line.tax_sub = 0
                            sale_order.order_line += purchase_order_line
                    if row_no > 1 :
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),sheet.row(row_no)))
                        if line[0]:
                            if line[1] == so_chung_tu:
                                product_id = self.env['product.product'].search([('default_code', '=', line[5])],limit=1)
                                product_uom_quantity = int(float(line[6]))
                                price_discount = float(line[10])
                                discount = float(line[9]) * 100
                                line_data = {
                                    'product_id': product_id.id,
                                    'product_uom': product_id.uom_id.id,
                                    'discount': discount,
                                }
                                count_order_line += 1
                                purchase_order_line = sale_order.order_line.new(line_data)
                                purchase_order_line.onchange_product_id()
                                purchase_order_line.price_discount = price_discount
                                purchase_order_line.price_unit = price_discount * 100 / (100 - discount)
                                purchase_order_line.product_qty = product_uom_quantity
                                tax = []
                                if line[8]:
                                    number_tax = int(float(line[8])*100)
                                    tax = self.env['account.tax'].search([('amount', '=', number_tax),('type_tax_use','=','purchase')], limit=1).ids
                                    if not tax:
                                        tax = self.env['account.tax'].search([('amount', '=', 0),('type_tax_use','=','purchase')], limit=1).ids
                                if tax:
                                    purchase_order_line.taxes_id = [(6, 0, tax)]
                                    if int(float(line[8])*100) in [0,5,10]:
                                        purchase_order_line.tax_sub = int(float(line[8])*100)
                                    else:
                                        purchase_order_line.tax_sub = 0
                                sale_order.order_line += purchase_order_line
                            if line[1] != so_chung_tu:
                                so_chung_tu = line[1]
                                date_order = datetime.utcfromtimestamp((float(line[0]) - 25569) * 86400.0)
                                date_planned = datetime.utcfromtimestamp((float(line[0]) - 25569) * 86400.0)
                                invoice_date_real = False
                                if line[2]:
                                    invoice_date_real = datetime.utcfromtimestamp((float(line[2]) - 25569) * 86400.0) or False
                                invoice_number_real = line[3] or False
                                partner_id = self.env['res.partner'].search([('name', '=', line[4]),('supplier','=',True)],limit=1)
                                product_id = self.env['product.product'].search([('default_code', '=', line[5])],limit=1)
                                product_uom_quantity = int(float(line[6]))
                                price_discount = float(line[10])
                                discount = float(line[9]) * 100
                                sale_order = self.env['purchase.order'].create({
                                    'partner_id': partner_id.id,
                                    'notes': so_chung_tu,
                                    'date_order' : date_order,
                                    'date_planned' : date_planned,
                                    'invoice_date_real': invoice_date_real,
                                    'invoice_number_real': invoice_number_real,
                                })
                                count_order += 1
                                line_data = {
                                    'product_id': product_id.id,
                                    'product_uom': product_id.uom_id.id,
                                    'discount': discount,
                                }
                                count_order_line += 1
                                purchase_order_line = sale_order.order_line.new(line_data)
                                purchase_order_line.onchange_product_id()
                                purchase_order_line.price_discount = price_discount
                                purchase_order_line.price_unit = price_discount * 100 / (100 - discount)
                                purchase_order_line.product_qty = product_uom_quantity
                                tax = []
                                if line[8]:
                                    number_tax = int(float(line[8])*100)
                                    tax = self.env['account.tax'].search([('amount', '=', number_tax),('type_tax_use','=','purchase')], limit=1).ids
                                    if not tax:
                                        tax = self.env['account.tax'].search([('amount', '=', 0),('type_tax_use','=','purchase')], limit=1).ids
                                if tax:
                                    purchase_order_line.taxes_id = [(6, 0, tax)]
                                    if int(float(line[8])*100) in [0,5,10]:
                                        purchase_order_line.tax_sub = int(float(line[8])*100)
                                    else:
                                        purchase_order_line.tax_sub = 0
                                sale_order.order_line += purchase_order_line

                print count_order
                print count_order_line
                print list_not_import

    # @api.multi
    # def import_xls(self):
    #     for record in self:
    #         if record.import_data:
    #             data = base64.b64decode(record.import_data)
    #             wb = open_workbook(file_contents=data)
    #             sheet = wb.sheet_by_index(0)
    #             list_customer = []

                # for row_no in range(sheet.nrows):
    #
    #                 # TODO import customer
    #                 if row_no >= 1:
    #                     line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
    #                             row.value), sheet.row(row_no)))
    #                     partner_id = self.env['res.partner'].search([('name','=',line[1])])
    #                     if partner_id:
    #                         partner_id.write({
    #                             'street'                  : line[2],
    #                             'feosco_business_license' : line[4],
    #                             'phone'                   : line[5],
    #                             'ref'                     : line[0],
    #                             'supplier': True,
    #                         })
    #                         print "----------------------------write" + str(row_no+1)
    #                     else:
    #                         partner_id.create({
    #                             'street'                    : line[2],
    #                             'feosco_business_license'   : line[4],
    #                             'phone'                     : line[5],
    #                             'ref'                       : line[0],
    #                             'name'                      : line[1],
    #                             'customer'                  : False,
    #                             'supplier': True,
    #                         })
    #                         print "**************************create" + str(row_no + 1)



                    # TODO update name product
                    # if row_no >= 1:
                    #     line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                    #         row.value), sheet.row(row_no)))
                    #     product_id = self.env['product.template'].search([('default_code','=',line[0])])
                    #     group_id = False
                    #     if line[11]:
                    #         group_id = self.env['product.group'].search([('name','=',line[11])])
                    #         if not group_id:
                    #             group_id = self.env['product.group'].create({
                    #                 'name' : line[11]
                    #             })
                    #     if not product_id:
                    #         raise UserError("not found" + str(row_no+1))
                    #     else:
                    #         product_id.name = line[2]
                    #         product_id.group_id = group_id.id
                    #         print row_no+1
    # @api.multi
    # def import_xls(self):
    #     for record in self:
    #         if record.import_data:
    #             data = base64.b64decode(record.import_data)
    #             wb = open_workbook(file_contents=data)
    #             sheet = wb.sheet_by_index(0)
    #             list_customer = []
    #         for row_no in range(sheet.nrows):
    #
    #             # TODO import group product sale
    #             if row_no == 0:
    #                 line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
    #                 for no in range(1, len(line)):
    #                     list_customer.append(line[no])
    #             if row_no >= 1:
    #                 line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
    #                     sheet.row(row_no)))
    #                 group_id = self.env['product.group.sale'].search([('name','=',line[0])])
    #                 if group_id.group_line_ids:
    #                     group_id.group_line_ids = None
    #                 if not group_id:
    #                     group_id = self.env['product.group.sale'].create({
    #                         'name' : line[0]
    #                     })
    #                 for no in range(0, len(line) - 1):
    #                     line_data = {
    #                         'partner_name' : list_customer[no],
    #                         'discount'     : float(line[no+1])*100
    #                     }
    #                     group_line = group_id.group_line_ids.new(line_data)
    #                     group_id.group_line_ids += group_line