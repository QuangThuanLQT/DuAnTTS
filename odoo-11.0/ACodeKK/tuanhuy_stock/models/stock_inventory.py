# -*- coding: utf-8 -*-

import base64
from xlrd import open_workbook
from odoo import models, fields, api

class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    import_data = fields.Binary(string="Tập tin")

    @api.multi
    def import_data_excel(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)

                line_ids = record.line_ids.browse([])
                row_error = []
                for row_no in range(sheet.nrows):
                    if row_no < 1:
                        continue
                    row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    product = self.env['product.product'].search([
                        '|', ('default_code', '=', row[0].strip()),
                        ('barcode', '=', row[0].strip())
                    ], limit=1)
                    if not product or int(float(row[1])) < 0:
                        row_error.append({
                            'default_code': row[0],
                            'price': '',
                            'qty': row[1],
                        })
                if row_error:
                    return {
                        'name': 'Import Warning',
                        'type': 'ir.actions.act_window',
                        'res_model': 'import.warning',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'data' : row_error,
                        }
                    }

                else:

                    for row_no in range(sheet.nrows):
                        if row_no < 1:
                            continue
                        row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                        if len(row) >= 2:
                            data = {
                                'product_qty': int(float(row[1])),
                                'location_id': record.location_id and record.location_id.id or False,
                            }
                            product = self.env['product.product'].search([
                                '|', ('default_code', '=', row[0].strip()),
                                ('barcode', '=', row[0].strip())
                            ], limit=1)
                            if product and product.id:
                                data['product_id'] = product.id
                                line_ids += record.line_ids.new(data)
                    record.line_ids = line_ids