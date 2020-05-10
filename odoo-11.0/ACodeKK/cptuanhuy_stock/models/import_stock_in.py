# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook
from datetime import datetime
class import_product_template(models.TransientModel):
    _name = 'import.stock.in'

    data_import = fields.Binary()
    picking_type_id = fields.Many2one('stock.picking.type', 'Loại giao nhận', required=1)

    def import_data_excel(self):
        try:
            data = base64.b64decode(self.data_import)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            # line_ids = self.planning_ids.browse([])
            for row_no in range(sheet.nrows):
                if row_no > 0:
                    row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                               sheet.row(row_no)))
                    if not row[7] or not row[2]:
                        raise UserError('Lỗi format file nhập')
                    else:
                        print row_no
                        picking_type_id = self.picking_type_id
                        if picking_type_id:
                            if picking_type_id.default_location_src_id:
                                location_id = picking_type_id.default_location_src_id.id
                            else:
                                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
                            if picking_type_id.default_location_dest_id:
                                location_dest_id = picking_type_id.default_location_dest_id.id
                            else:
                                location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
                        min_date = datetime.fromtimestamp((float(row[0]) - 25569) * 86400.0)
                        sale_select_id = self.env['sale.order'].search([('name', '=', row[5])], limit=1)
                        mrp_production = self.env['mrp.production'].search([('name', '=', row[6])], limit=1)
                        if not type(location_id) is int:
                            location_id = location_id.id
                        if not type(location_dest_id) is int:
                            location_dest_id = location_dest_id.id
                        picking_data = {
                            'picking_type_id': picking_type_id.id,
                            'note': row[3],
                            'location_id': location_id,
                            'location_dest_id': location_dest_id,
                            'origin': row[4],
                            'min_date': min_date,
                            'sale_select_id': sale_select_id and sale_select_id.id or False,
                            'mrp_production': mrp_production and mrp_production.id or False
                        }

                        picking_line = []
                        if row_no == 20:
                            True
                        product_id = self.env['product.product'].search([('default_code', '=', row[7])], limit=1)
                        if not product_id:
                            print row[5]
                            continue
                        if row[6]:
                            product_uom = self.env['product.uom'].search([('name', '=', row[8])], limit=1)
                            if not product_uom:
                                product_uom = product_id.uom_id
                        line_data = {
                            'product_id': product_id.id,
                            'name': product_id.name,
                            'product_uom_qty': row[10],
                            'product_uom': product_id.uom_id.id,
                            'procure_method': 'make_to_stock',
                            'warehouse_id': picking_type_id.warehouse_id.id,
                            'location_id': location_id,
                            'location_dest_id': location_dest_id,
                            'date': min_date,
                        }
                        picking_data['move_lines'] = [(0, 0, line_data)]
                        picking_id = self.env['stock.picking'].search([('name', '=', row[2])], limit=1)
                        if not picking_id:
                            picking_id = self.env['stock.picking'].create(picking_data)
                            picking_id.name = row[2]
                            print 'row %s - create picking' % row_no
                        else:
                            line_data['picking_id'] = picking_id.id
                            move_line = self.env['stock.move'].create(line_data)
                            print 'row %s - add move line' % row_no
        except:
            raise UserError('Lỗi format file nhập')
