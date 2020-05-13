# -*- coding: utf-8 -*-

from odoo import models, fields, api


class product_template(models.Model):
    _inherit = 'product.template'

    is_manual_barcode = fields.Boolean('Nhập tay', compute='_compute_manual_barcode', store=True)
    purchase_code = fields.Char('Mã mua hàng')
    list_price = fields.Float(track_visibility='onchange')
    barcode = fields.Char('Barcode', store=False)
    barcode_text = fields.Char('Barcodes', readonly=True, store=True)


    @api.depends('barcode')
    def _compute_manual_barcode(self):
        for record in self:
            manually = True
            if record.barcode:
                if record.barcode.isdigit():
                    if 10000 <= int(record.barcode) <= 99999:
                        manually = False
            else:
                manually = False
            record.is_manual_barcode = manually
