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
    location_id = fields.Many2one(domain=[('usage','=','internal')],required="1")

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

class mrp_routing_workcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    code        = fields.Char(string='Mã công việc', required=True)
    code_before = fields.Many2many('mrp.routing.workcenter', 'mrp_routing_workcenter_ref_m2m', 'id_1', 'id_2', domain="[('routing_id','=',routing_id),('id','!=',id)]",string="Công việc trước")
    user_id     = fields.Many2one('res.users',string="Người phụ trách")

    _sql_constraints = [('unique_code', 'UNIQUE(code)', 'Mã công việc là duy nhất.')]
    routing_id = fields.Many2one(required=0)

    @api.multi
    def name_get(self):
        res = []
        for field in self:
            res.append((field.id, '%s' % (field.code)))
        return res

    @api.model
    def default_get(self, fields):
        res = super(mrp_routing_workcenter, self).default_get(fields)
        res['code'] = self.env['ir.sequence'].next_by_code('workorder.code')
        return res

    @api.model
    def update_sequence_code(self):
        routing_workcenters = self.search([])
        for routing_workcenter in routing_workcenters:
            if not routing_workcenter.code:
                routing_workcenter.code = self.env['ir.sequence'].next_by_code('workorder.code')
        return True