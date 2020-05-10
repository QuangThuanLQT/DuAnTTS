# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook

class import_product_template(models.TransientModel):
    _name = 'import.product'

    data_import = fields.Binary()

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
                    if not row[0] or not row[2] or not row[3]:
                        raise UserError('Lỗi format file nhập')
                    else:
                        product_data = {
                            'default_code': row[0],
                            'name': row[2],
                            'purchase_code': row[4] or "",
                            'list_price': float(row[7]) or 1,
                            'standard_price': float(row[8]) or 1,
                        }
                        uom_id = self.env['product.uom'].search([('name', '=', row[3])], limit=1)
                        if uom_id:
                            product_data['uom_id'] = uom_id.id
                            product_data['uom_po_id'] = uom_id.id
                        if row[5]:
                            brand_name_select = self.env['brand.name'].search([('name', '=', row[5])])
                            if not brand_name_select:
                                brand_name_select = self.env['brand.name'].create({
                                    'name': row[5]
                                })
                            product_data['brand_name_select'] = brand_name_select.id
                        if row[9]:
                            group_id = self.env['product.group'].search([('name', '=', row[9])])
                            if not group_id:
                                group_id = self.env['product.group'].create({
                                    'name': row[9]
                                })
                            product_data['group_id'] = group_id.id
                        if len(row) > 11:
                            product_data['is_pack'] = True,
                            wk_product_pack = []
                            for i in range(11, len(row), 2):
                                child_product = self.env['product.product'].search([('default_code', '=', row[i])], limit=1)
                                if child_product:
                                    child_data = {
                                        'product_name': child_product.id,
                                        'product_quantity': int(float(row[i+1])) if len(row) >= (i+1) else 1
                                    }
                                    wk_product_pack.append((0, 0, child_data))
                            product_data['wk_product_pack'] = wk_product_pack
                        product_id = self.env['product.template'].search([('default_code', '=', row[0])], limit=1)
                        if not product_id:
                            product_id = self.env['product.template'].create(product_data)
                        else:
                            product_id.wk_product_pack.unlink()
                            product_id.write(product_data)
            #             line = self.planning_ids.new(line_data)
            #             line_ids += line
            # self.planning_ids += line_ids
        except:
            raise UserError('Lỗi format file nhập')