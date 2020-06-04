# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class nhap_hang(models.Model):
    _name = 'nhap.hang'

    partner_id = fields.Many2one('res.partner', string='Nhà cung cấp', domain=[('supplier', '=', True)])
    ngay_yeu_cau = fields.Datetime(string='Ngày yêu cầu', default=fields.Datetime.now)
    thong_tin_nhap_id = fields.One2many('thong.tin.nhap.hang', 'thong_tin_nhap_ids')

    # truyen du lieu qua mua hang
    @api.multi
    def action_confirm(self):
        if self.partner_id:
            purchase_id = self.env['purchase.order'].create({
                'partner_id': self.partner_id.id
            })
            for line in self.thong_tin_nhap_id:
                pur_line_obj = self.env['purchase.order.line']
                pur_line_data = pur_line_obj.default_get(pur_line_obj._fields)
                pur_line_data.update({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'date_planned': datetime.now(),
                    'product_uom': line.product_id.uom_id.id
                })
                purchase_id.order_line += purchase_id.order_line.new(pur_line_data)


class thong_tin_nhap(models.Model):
    _name = 'thong.tin.nhap.hang'

    thong_tin_nhap_ids = fields.Many2one('nhap.hang')
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    invoice_name = fields.Char(string='Tên Hoá Đơn')
    product_uom_qty = fields.Float(string='SL cần nhập', default=1.0)
    price_unit = fields.Float(string='Đơn giá', default=0.0)
    price_subtotal = fields.Float(string='Tổng phụ', compute='_compute_amount', default=0.0)

    @api.depends('price_unit', 'product_uom_qty', 'price_subtotal')
    def _compute_amount(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.product_uom_qty
