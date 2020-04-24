# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class stock_picking_history(models.Model):
    _name = 'stock.picking.history'

    picking_name = fields.Char(string="Phiếu kho")
    date_history = fields.Date(string="Ngày")
    product_id = fields.Many2one('product.product',string="Sản phẩm")
    product_uom_qty = fields.Float(string="Số lượng")
    product_qty_reserve = fields.Float(string="SL giữ chỗ")
    product_qty_missing = fields.Float(string="SL còn thiếu")
    state = fields.Selection([
        ('draft', 'Mới'), ('cancel', 'Đã huỷ'),
        ('waiting', 'Chờ dịch chuyển khác'),
        ('confirmed', 'Chờ có hàng'),
        ('assigned', 'Có sẵn')])
    partner_id = fields.Many2one('res.partner',string="Đối tác")
    origin = fields.Char(string="Tài liệu nguồn")

    def create_stock_picking_history(self):
        picking_ids = self.env['stock.picking'].search([('state','not in',['done','draft'])])
        for picking_id in picking_ids:
            for line in picking_id.move_lines:
                data = {
                    'picking_name' : picking_id.name,
                    'date_history': datetime.now().date(),
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_qty_reserve': line.product_qty_reserve,
                    'product_qty_missing': line.product_qty_missing,
                    'state': line.state,
                    'partner_id': picking_id.partner_id.id,
                    'origin': picking_id.origin,
                }

                self.env['stock.picking.history'].create(data)