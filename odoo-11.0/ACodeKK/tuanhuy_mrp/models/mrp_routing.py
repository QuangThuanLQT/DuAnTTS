# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class mrp_routing(models.Model):
    _inherit = 'mrp.routing'

    routing_wokcenter_data = fields.Binary(string="Tải file của bạn lên")

    def clear_routing_wokcenter_data(self):
        if self.operation_ids:
            self.operation_ids.unlink()

    def import_routing_wokcenter_data(self):
        try:
            data = base64.b64decode(self.routing_wokcenter_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            line_ids = self.operation_ids.browse([])
            for row_no in range(sheet.nrows):
                if row_no > 0:
                    row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                               sheet.row(row_no)))
                    if not row[0] or not row[1]:
                        raise UserError('Lỗi format file nhập')
                    else:
                        workcenter_id = self.env['mrp.workcenter'].search([('name', '=', row[1])], limit=1)
                        if not workcenter_id:
                            workcenter_id = self.env['mrp.workcenter'].create({
                                'name': row[1]
                            })
                        line_data = {
                            'name': row[0],
                            'workcenter_id': workcenter_id.id,
                            'time_cycle_manual': float(row[2]) if row[2] else 0
                        }
                        line = self.operation_ids.new(line_data)
                        line_ids += line
            self.operation_ids += line_ids
        except:
            raise UserError('Lỗi format file nhập')