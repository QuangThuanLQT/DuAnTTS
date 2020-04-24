# -*- coding: utf-8 -*-

import base64
from xlrd import open_workbook
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    barcode = fields.Char(related='product_id.barcode')

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'barcodes.barcode_events_mixin']

    import_data = fields.Binary(string="Tập tin")

    def on_barcode_scanned(self, barcode):
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            corresponding_line = self.order_line.filtered(lambda r: r.product_id.barcode == barcode)
            if corresponding_line:
                corresponding_line[0].product_uom_qty += 1
            else:
                line = self.order_line.new({
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': 1.0,
                    'price_unit': product.lst_price,
                })
                line.product_id_change()
                line.product_uom_change()
                self.order_line += line
            return

    @api.multi
    def import_data_excel(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)

                order_line = record.order_line.browse([])

                row_error = []
                for row_no in range(sheet.nrows):
                    if row_no > 0:
                        row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                        product = self.env['product.product'].search([
                            '|', ('default_code', '=', row[0].strip()),
                            ('barcode', '=', row[0].strip())
                        ], limit=1)
                        if not product or int(float(row[1]))< 0:
                            row_error.append({
                                'default_code' : row[0],
                                'price': row[2] or False,
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
                        if row_no > 0:
                            row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                            if len(row) >= 2:
                                product = self.env['product.product'].search([
                                    '|', ('default_code', '=', row[0].strip()),
                                    ('barcode', '=', row[0].strip())
                                ], limit=1)
                                if product and product.id:
                                    line_data = {
                                        'product_id': product.id,
                                        'product_uom': product.uom_id.id,
                                        'price_unit': product.lst_price,
                                        'product_uom_qty': int(float(row[1])),
                                    }
                                    if row[2]:
                                        discount = float(row[2])
                                        line_data['discount'] = discount
                                        if row[3]:
                                            raise ValidationError(_('Không được có cả chiết khấu và giá đã chiết khấu.'))
                                    elif row[3]:
                                        price_discount = float(row[3])
                                        line_data['price_discount'] = price_discount
                                    line = record.order_line.new(line_data)
                                    line.product_id_change()
                                    line.product_uom_change()
                                    if not row[2] and not row[3]:
                                        line.onchange_product_for_ck(self.partner_id.id)
                                    order_line += line
                    record.order_line = order_line