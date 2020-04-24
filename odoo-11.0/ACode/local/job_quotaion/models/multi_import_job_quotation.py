# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import base64
from xlrd import open_workbook
from odoo.exceptions import UserError
import base64
import StringIO
import xlsxwriter

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class import_job_quotation(models.TransientModel):
    _name = 'import.job.quotation'

    import_data = fields.Binary(string="File Import")

    @api.multi
    def import_xls(self):
        for record in self:
            try:
                if record.import_data:
                    data = base64.b64decode(record.import_data)
                    wb = open_workbook(file_contents=data)
                    sheet = wb.sheet_by_index(0)
                    job_quotaion_id = self.env['job.quotaion']
                    type = False

                    for row_no in range(sheet.nrows):
                        if row_no > 1:
                            row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                                row.value),
                                       sheet.row(row_no)))
                            if not row[0] and not row[1] and not row[8]:
                                break
                            if row[0]:
                                if row[1].strip():
                                    job_quotaion_id = self.env['job.quotaion'].create({
                                        'name' : row[1].strip()
                                    })
                                    type = False
                                    continue
                                else:
                                    raise UserError('Lỗi format file nhập')
                            if not job_quotaion_id:
                                raise UserError('Lỗi format file nhập')
                            else:
                                if row[1]:
                                    if row[1] and not row[2] and not row[3] and not row[4] and not row[5] and not row[
                                        6] and not row[7] and not row[8]:
                                        type = row[1]
                                        type_id = self.env['job.type'].search([('name', '=', type)], limit=1)
                                        if not type_id:
                                            type_id = self.env['job.type'].create({
                                                'name': type,
                                                'job_type': 'material',
                                                'code': type,
                                            })
                                        type = type_id
                                    else:
                                        product_uom_id = False
                                        if row[7]:
                                            self.env.cr.execute(
                                                "SELECT id FROM product_uom WHERE lower(name) = '%s'" % (
                                                row[7].strip().lower()))
                                            brand_names = self.env.cr.fetchall()
                                            if brand_names:
                                                product_uom_id = brand_names[0][0]
                                        line_data = {
                                            'type': type and type.id or False,
                                            'description': row[1],
                                            'key_word': row[2],
                                            'nha_san_xuat': row[3],
                                            'ma_san_pham': row[4],
                                            'xuat_su': row[5],
                                            'ma_dat_hang': row[6],
                                            'product_uom': product_uom_id if product_uom_id else False,
                                            'so_luong': row[8],
                                            'note': row[9],
                                        }
                                        line = job_quotaion_id.line_ids.new(line_data)
                                        line.onchange_product_id()
                                        job_quotaion_id.line_ids += line

            except:
                raise UserError('Lỗi format file nhập')


