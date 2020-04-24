# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_order_return(models.Model):
    _inherit = 'sale.order.return'

    state_log_ids = fields.One2many('state.log', 'sale_id')


class nhat_ky_lich_su(models.Model):
    _name = 'state.log'

    sale_id = fields.Many2one('sale.order.return')
    sequence = fields.Integer('Sequence')
    date = fields.Datetime(string='Ngày')
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
    ], string='Tình trạng hoạt động')
