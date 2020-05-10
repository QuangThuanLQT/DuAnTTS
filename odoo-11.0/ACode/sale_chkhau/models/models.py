# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_chkhau(models.Model):
    _inherit = 'sale.order.line'

    chieckhau = fields.Integer(string="Chiết khấu")
    loai_chkhau = fields.Selection([('theoSL','Theo số lượng'),('theoPT','Theo %')],string="Loại chiết khấu")

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'chieckhau','loai_chkhau')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            price_subtotal_1 = taxes['total_excluded']
            if (line.loai_chkhau =='theoSL'):
                price_subtotal_1 = (line.product_uom_qty - line.chieckhau)* line.price_unit
            if (line.loai_chkhau == 'theoPT'):
                chkhau = float(self.chieckhau)/100
                price_subtotal_1 = line.product_uom_qty* line.price_unit*(1 - chkhau)

            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': price_subtotal_1,
            })