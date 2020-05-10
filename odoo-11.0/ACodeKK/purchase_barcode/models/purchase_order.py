# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    barcode = fields.Char(related='product_id.barcode')

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'barcodes.barcode_events_mixin']

    def on_barcode_scanned(self, barcode):
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            corresponding_line = self.order_line.filtered(lambda r: r.product_id.barcode == barcode)
            if corresponding_line:
                corresponding_line[0].product_qty += 1
            else:
                line = self.order_line.new({
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    'product_qty': 1.0,
                    'price_unit': product.standard_price,
                    'date_planned': fields.Datetime.now(),
                })
                line.onchange_product_id()
                self.order_line += line
            return