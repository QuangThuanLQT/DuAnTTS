# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
#import StringIO
import xlsxwriter
from odoo.exceptions import UserError

from xlrd import open_workbook
import os

class import_warning(models.TransientModel):
    _name = 'import.warning'

    import_warning_ids = fields.One2many('import.warning.line','import_warning_id')
    import_product_warning_ids = fields.One2many('import.product.warning.line', 'import_warning_id')
    check_show_warning = fields.Boolean(default=False)

    @api.model
    def default_get(self, fields):
        res = super(import_warning, self).default_get(fields)
        if 'data' in self._context:
            data_line = []
            for line in self._context.get('data'):
                data_line.append((0,0,line))
            res['import_warning_ids'] = data_line
            res['check_show_warning'] = False
        if 'data_product' in self._context:
            data_line = []
            for line in self._context.get('data_product'):
                data_line.append((0,0,line))
            res['import_product_warning_ids'] = data_line
            res['check_show_warning'] = True
        return res

    @api.multi
    def export_file(self):

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Dong khong the nhap')
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '8', 'align': 'center', 'valign': 'vcenter','font_name': 'Times New Roman'})
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:C', 15)
        row = 0
        summary_header = ['Ma Noi Bo','SL Dat','Gia Da CK']

        [worksheet.write(row, header_cell, summary_header[header_cell], header_bold_color) for header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]
        for line in self.import_warning_ids:
            row += 1
            worksheet.write(row, 0, line.default_code)
            worksheet.write(row, 1, line.qty)
            worksheet.write(row, 2, line.price)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'dong_khong_the_nhap.xlsx', 'datas_fname': 'dong_khong_the_nhap.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    @api.multi
    def export_product_file(self):

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('San Pham Da Ton Tai')
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '8', 'align': 'center', 'valign': 'vcenter', 'font_name': 'Times New Roman'})
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:C', 40)
        row = 0
        summary_header = ['Ma Noi Bo', 'Ten']

        [worksheet.write(row, header_cell, summary_header[header_cell], header_bold_color) for header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]
        for line in self.import_product_warning_ids:
            row += 1
            worksheet.write(row, 0, line.default_code)
            worksheet.write(row, 1, line.name)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'san_pham_da_ton_tai.xlsx', 'datas_fname': 'san_pham_da_ton_tai.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    @api.multi
    def keep_import(self):
        order = self.env[self._context['active_model']].browse(self._context['active_id'])
        data = base64.b64decode(order.import_data)
        wb = open_workbook(file_contents=data)
        sheet = wb.sheet_by_index(0)
        order_line = order.order_line.browse([])
        row_error = []
        for row_no in range(sheet.nrows):
            if row_no > 0:
                row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                           sheet.row(row_no)))
                if len(row) >= 5:
                    product = self.env['product.product'].search([
                        '|', ('default_code', '=', row[0].strip()),
                        ('barcode', '=', row[0].strip())
                    ], limit=1)
                    if not product or float(row[4]) < 0 or int(float(row[3])) < 0:
                        row_error.append(row_no)
        for row_no in range(sheet.nrows):
            if row_no in row_error:
                continue
            else:
                row = (
                    map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                if len(row) >= 5:
                    product = self.env['product.product'].search([
                        '|', ('default_code', '=', row[0].strip()),
                        ('barcode', '=', row[0].strip())
                    ], limit=1)
                    if product and product.id:
                        line_data = {
                            'product_id': product.id,
                            'product_uom': product.uom_id.id,
                            'name': row[1].strip() or product.name,
                            'price_discount': float(row[4]),
                            'product_uom_qty': int(float(row[3])),
                            'product_qty': int(float(row[3])),
                        }
                        line = order.order_line.new(line_data)
                        line.onchange_product_id()
                        line.product_qty = int(float(row[3]))
                        line.price_unit = float(row[4]) or product.lst_price
                        order_line += line
        order.order_line = order_line


    @api.multi
    def create_product_import(self):
        order = self.env[self._context['active_model']].browse(self._context['active_id'])
        data = base64.b64decode(order.import_data)
        wb = open_workbook(file_contents=data)
        sheet = wb.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            if row_no > 0:
                row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                if len(row) >= 6:
                    product = self.env['product.product'].search([
                        '|', ('default_code', '=', row[0].strip()),
                        ('barcode', '=', row[0].strip())
                    ], limit=1)
                    if not product or float(row[5]) < 0 or int(float(row[4])) < 0:
                        if not product:
                            uom_id = False
                            if row[3]:
                                uom_id = self.env['product.uom'].search([('name', '=', row[3])], limit=1).id
                            product_id = self.env['product.product'].create({
                                'name': row[1] or row[0].strip(),
                                'default_code': row[0].strip(),
                                'uom_id': uom_id or self.env['product.uom'].search([('name', '=', 'Cái')], limit=1).id,
                                'uom_po_id': uom_id or self.env['product.uom'].search([('name', '=', 'Cái')], limit=1).id
                            })

        # order.import_data_excel()

class import_warning_line(models.TransientModel):
    _name = 'import.warning.line'

    default_code = fields.Char(string='Default Code')
    price = fields.Char(string='Price')
    qty = fields.Char(string='Quantity')
    import_warning_id = fields.Many2one('import.warning')

class import_product_warning_line(models.TransientModel):
    _name = 'import.product.warning.line'

    default_code = fields.Char(string='Default Code')
    name = fields.Char(string='Name')
    import_warning_id = fields.Many2one('import.warning')

