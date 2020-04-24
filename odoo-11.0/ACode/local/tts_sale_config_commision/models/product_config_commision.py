# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product_product_ihr(models.Model):
    _inherit = 'product.product'

    commision = fields.Float(string="% Thưởng/sản phẩm")
    trang_thai_hd = fields.Selection([
        ('active', 'Đang kinh doanh'),
        ('unactive', 'Ngừng kinh doanh')
    ], compute='get_trang_thai_hd', string='Trạng thái', store=True)

    @api.depends('active')
    def get_trang_thai_hd(self):
        for rec in self:
            if rec.active:
                rec.trang_thai_hd = 'active'
            else:
                rec.trang_thai_hd = 'unactive'
