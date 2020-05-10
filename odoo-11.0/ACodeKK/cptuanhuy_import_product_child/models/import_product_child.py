# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook

class import_product_template(models.TransientModel):
    _name = 'import.product.child'

    data_import = fields.Binary()
    not_find_product =fields.Char()
    not_find_pk =fields.Char()

    def import_data_excel(self):
        try:
            data = base64.b64decode(self.data_import)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            # line_ids = self.planning_ids.browse([])
            # pk_list = []
            not_find_product = []
            not_find_pk = []
            # index_sp = False
            # for header in sheet.row_values(0):
            #     if 'Phụ kiện' in header:
            #         pk_list.append(sheet.row_values(0).index(header))
            #     if 'Mã sản phẩm' in header.encode('utf-8'):
            #         index_sp = sheet.row_values(0).index(header)
            # if index_sp == False:
            #     raise UserError('Không tìm thấy Mã sản phẩm')
            # if not pk_list:
            #     raise UserError('Không tìm thấy Phụ kiện')
            for rownum in range(1, sheet.nrows):
                product_code = str(sheet.row_values(rownum)[0])
                product      = self.env['product.template'].search([
                    ('default_code', '=', product_code.strip())
                ])
                if product and len(product) == 1:
                    for pk_col in range(1,sheet.ncols):
                        pk_val = str(sheet.row_values(rownum)[pk_col])
                        if pk_val:
                            pk_product = self.env['product.template'].search([('default_code', '=', pk_val.strip())])
                            if pk_product and len(pk_product) == 1:

                                for line in product.child_ids:
                                    if line.product_id.id == pk_product.id:
                                        line.unlink()

                                product.write({
                                    'child_ids': [(0, 0, {'product_id': pk_product.id})]
                                })
                            else:
                                not_find_pk.append(pk_val)
                else:
                    not_find_product.append(product_code)
                    
            self.not_find_product = ''.join(str(line) + ' ,' for line in  not_find_product)
            self.not_find_pk = ''.join(str(line) + ' ,' for line in  not_find_pk)
            if not_find_product or not_find_pk:
                return {
                    'type': 'ir.actions.act_window',
                    'name': "Sản phẩm không tìm thấy",
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'import.product.child',
                    'res_id'   : self.id,
                    'view_id'  : self.env.ref("cptuanhuy_import_product_child.import_product_child_view_result").id,
                    'target'   : 'new'
                }

        except:
            raise UserError('Lỗi format file nhập')



