from odoo import fields, models, api, _
import base64
from xlrd import open_workbook
from odoo.exceptions import UserError


class import_purchase_order(models.TransientModel):
    _name = 'import.stock.inventory'

    stock_inventory_id = fields.Many2one('stock.inventory', string="Stock Inventory")
    import_data = fields.Binary(string="File Import")

    @api.multi
    def check_import_file(self):
        for record in self:
            data = base64.b64decode(record.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)

            for row_no in range(sheet.nrows):
                if row_no == 0:
                    continue
                row = (
                    map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))

                product = self.env['product.product'].search([('default_code', '=', row[0].strip())
                                                              ], limit=1)
                if not product:
                    raise UserError('Not found product %s - %s' % (row[0].strip(), row_no + 1))

    @api.multi
    def import_xls(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)
                line_ids = []
                count = 0

                for row_no in range(sheet.nrows):
                    if row_no == 0:
                        continue
                    row = (
                        map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))

                    product_qty = int(float(row[1]))

                    data = {
                        'product_qty': product_qty,
                        'location_id': record.stock_inventory_id.location_id and record.stock_inventory_id.location_id.id or False,
                        'theoretical_qty': product_qty,
                    }
                    product = self.env['product.product'].search([('default_code', '=', row[0].strip())
                                                                  ], limit=1)
                    if product and product.id:
                        data['product_id'] = product.id
                        data['product_uom_id'] = product.uom_id.id
                        line_ids.append((0, 0, data))
                        count += 1
                        print
                        row_no + 1
                if record.stock_inventory_id.state == 'draft':
                    record.stock_inventory_id.state = 'confirm'
                    record.stock_inventory_id.date = fields.Datetime.now()
                record.stock_inventory_id.write({'line_ids': line_ids})
                print
                "KQ-----------------" + str(count)
