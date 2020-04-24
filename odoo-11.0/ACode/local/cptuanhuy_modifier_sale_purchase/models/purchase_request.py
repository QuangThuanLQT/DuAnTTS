# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class purchase_request_line(models.Model):
    _inherit = 'purchase.request.line'

    approved_by     = fields.Many2one('res.users',string='Approved by')
    deadline        = fields.Date(string='Deadline')
    receive_date    = fields.Date(string='Ngày nhận hàng')
    sale_id         = fields.Many2one('sale.order',string='Đơn hàng')
    request_amount  = fields.Float(string='Tổng giá trị mua hàng',compute='get_request_amount')
    state           = fields.Selection([('open','Mở'),('close','Đóng')],string='Trạng thái Request',default='open')
    color           = fields.Char(compute='get_color_view')

    @api.multi
    def get_color_view(self):
        for record in self:
            record.color = ''
            if record.state == 'open':
                # Request đã lên PO mua: màu xanh
                if record.purchase_lines and len(record.purchase_lines.ids) > 0:
                    record.color = 'green'
                else:
                    # Request mà [Deadline - « ngày hiện tại »<=3] ngày đến Deadline mà chưa có PO mua hàng: màu hồng
                    if record.deadline and len(record.purchase_lines) == 0:
                        deadline    = datetime.datetime.strptime(record.deadline,DEFAULT_SERVER_DATE_FORMAT).date()
                        current_day = datetime.datetime.now().date()
                        if (deadline - current_day).days <= 3:
                            record.color = 'pink'
                    else:
                        # Request chưa lên PO mua: màu cam
                        record.color = 'orange'
            # Request:  Deadline< ngày hàng về: màu đỏ
            if record.deadline and record.receive_date and record.deadline < record.receive_date:
                record.color = 'red'


    @api.depends('purchase_lines')
    def get_request_amount(self):
        for record in self:
            record.request_amount = sum([line.price_subtotal for line in record.purchase_lines])

    @api.multi
    def action_request_state(self):
        for record in self:
            if self.state == 'open':
                self.state = 'close'
            else:
                self.state = 'open'

    @api.multi
    def multi_request_close(self):
        if self.env.context.get('active_ids',False) and self.env.context.get('active_model') == 'purchase.request.line':
            self.env['purchase.request.line'].browse(self.env.context.get('active_ids',False)).write({'state': 'close'})

    @api.multi
    def multi_request_open(self):
        if self.env.context.get('active_ids', False) and self.env.context.get('active_model') == 'purchase.request.line':
            self.env['purchase.request.line'].browse(self.env.context.get('active_ids', False)).write({'state': 'open'})

class purchase_request(models.Model):
    _inherit = 'purchase.request'

    deadline = fields.Date('Deadline')

    @api.onchange('deadline')
    def get_deadline_for_line(self):
        for line in self.line_ids:
            line.deadline = self.deadline