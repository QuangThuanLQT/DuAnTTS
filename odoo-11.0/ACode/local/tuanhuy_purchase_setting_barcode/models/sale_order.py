# -*- coding: utf-8 -*-

from odoo import models, fields, api

class purchase_order_inherit(models.Model):
    _inherit = 'sale.order'

    ma_bin = fields.Char()
    check_show_ma_bin = fields.Boolean(compute="_get_check_show_ma_bin")
    check_show_add_line = fields.Boolean(compute="_get_check_show_ma_bin")
    check_used_ma_bin = fields.Boolean(default=False,string="Nhập bằng tay")

    @api.onchange('ma_bin')
    def _get_check_show_ma_bin(self):
        for record in self:
            if self.env['ir.values'].get_default('sale.config.settings', 'allow_input_barcode') == 'allow':
                record.check_show_ma_bin = True
                list_ma_pin = self.env['res.users'].search([('ma_bin', '!=', False)]).mapped('ma_bin')
                if record.ma_bin and record.ma_bin in list_ma_pin:
                    record.check_show_add_line = True
                    record.check_used_ma_bin = True
                else:
                    record.check_show_add_line = False
            else:
                record.check_show_ma_bin = False
                record.check_show_add_line = True

    @api.model
    def create(self, vals):
        res = super(purchase_order_inherit, self).create(vals)
        if self.env['ir.values'].get_default('sale.config.settings', 'allow_input_barcode') == 'allow':
            res.ma_bin = None
            res.check_show_add_line = False
        return res

    @api.multi
    def write(self, vals):
        if self.env['ir.values'].get_default('sale.config.settings', 'allow_input_barcode') == 'allow':
            vals.update({
                'ma_bin' : '',
                'check_show_add_line' : False,
            })
        res = super(purchase_order_inherit, self).write(vals)
        return res

class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    allow_input_barcode = fields.Selection([
        ('allow', 'Sử dụng'),
        ('unallow', 'Không sử dụng')
    ], 'Kiểm tra cho phép nhập Barcode',
        default='unallow')

    @api.multi
    def set_allow_input_barcode_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'allow_input_barcode', self.allow_input_barcode)