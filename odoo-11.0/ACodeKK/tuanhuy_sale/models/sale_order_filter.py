# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_order_filter(models.TransientModel):
    _name = "sale.order.filter"

    partner_id = fields.Many2one('res.partner', 'Khách Hàng', required=True)
    start_date = fields.Date('Ngày bắt đầu')
    end_date = fields.Date('Ngày kết thúc')
    order_ids = fields.Many2many('sale.order', string='Đơn Hàng')

    def filter_order_by_partner(self):
        self.order_ids = False
        conditions = []
        conditions.append(('partner_id', '=', self.partner_id.id))
        if self.start_date:
            conditions.append(('confirmation_date', '>=', self.start_date))
        if self.end_date:
            conditions.append(('confirmation_date', '<=', self.end_date))
        orders = self.env['sale.order'].search(conditions)
        if orders:
            self.order_ids = orders
        return {
            "type": "ir.actions.do_nothing",
        }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     'view_type': 'form',
        #     'res_model': 'sale.order.filter',
        #     'target': 'new',
        # }