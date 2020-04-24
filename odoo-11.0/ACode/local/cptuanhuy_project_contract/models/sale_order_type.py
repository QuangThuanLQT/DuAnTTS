# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class sale_order_type(models.Model):
    _name = "sale.order.type"

    name = fields.Char(string="Tên")
    type = fields.Selection(string='Loại', selection=[
        ('sanxuat', 'Sản xuất'),
        ('thuongmai', 'Thương mại'),
    ], default='thuongmai')
    account_analytic_tag_ids = fields.Many2many('account.analytic.tag',string="Doanh thu")
    cost_account_analytic_tag_ids = fields.Many2many('account.analytic.tag','sale_type_analytic_tag_ref', 'so_ty_id', 'tag_id', string="Chi Phí")
