# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import calendar

class product_vendor_price(models.Model):
    _name = 'product.vendor.price'

    name = fields.Char(string="Tên")
    partner_id = fields.Many2one('res.partner', string='Nhà cung cấp')
    date_from = fields.Date(string='Ngày bắt đầu')
    date_to = fields.Date(string='Ngày kết thúc')

    seller_ids = fields.One2many('product.supplierinfo', 'product_price_id', 'Sản phẩm')

    @api.model
    def default_get(self, fields):
        res = super(product_vendor_price, self).default_get(fields)
        if 'active_id' in self._context:
            product_vendors = self.env['res.partner'].browse(self._context['active_id'])
            res['partner_id'] = product_vendors.id

            today = datetime.today()
            res['date_from'] = today.replace(day=1).strftime('%Y-%m-%d')

            res['date_to'] = today.replace(day=calendar.monthrange(today.year, today.month)[1]).strftime('%Y-%m-%d')

        return res

    @api.onchange('date_from', 'date_to')
    def _onchange_date_from(self):

        for i in self.seller_ids:
            i.date_start = self.date_from
            i.date_end = self.date_to

    def button_upload_function(self):
        return {
            'name': 'Tải lên tập tin',
            'domain': [],
            'res_model': 'product.vendor.price.file',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {},
            'target': 'new',
        }