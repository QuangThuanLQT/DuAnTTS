# -*- coding: utf-8 -*-

from odoo import models, fields, api


class state_log(models.Model):
    _name = 'state.log'

    sequence = fields.Integer('Sequence')
    date = fields.Datetime('Date')
    state = fields.Selection([
        ('waiting_pick', 'Chờ thu cọc'),
        ('ready_pick', 'Chờ lấy hàng'),
        ('picking', 'Đang lấy hàng'),
        ('waiting_pack', 'Chờ đóng gói'),
        ('packing', 'Đang đóng gói'),
        ('waiting_delivery', 'Chờ giao hàng'),
        ('delivery', 'Đang giao hàng'),
        ('reveive', 'Chờ nhận hàng'),
        ('waiting', 'Chờ kiểm hàng'),
        ('checking', 'Đang kiểm hàng'),
        ('done', 'Hoàn tất'),
        ('reverse_tranfer', 'Reverse Tranfer'),
        ('cancel', 'Huỷ'),
        ('block', 'Khóa đơn hàng')
    ], string='Operation Status')
    sale_id = fields.Many2one('sale.order')
    purchase_id = fields.Many2one('purchase.order')
