# -*- coding: utf-8 -*-

from odoo import models, fields, api

class purchase_order_inherit(models.Model):
    _inherit = 'purchase.order'

    ma_bin = fields.Char()
    check_show_ma_bin = fields.Boolean(compute="_get_check_show_ma_bin")
    check_show_add_line = fields.Boolean(compute="_get_check_show_ma_bin")
    check_used_ma_bin = fields.Boolean(default=False,string="Nhập bằng tay")

    @api.model
    def get_check_add_line(self,ma_bin,model):
        setting_check = False
        if model == 'sale.order' or model == 'sale.order.line':
            setting_check = self.env['ir.values'].get_default('sale.config.settings', 'allow_input_barcode')
        if model == 'purchase.order' or model == 'purchase.order.line':
            setting_check = self.env['ir.values'].get_default('purchase.config.settings', 'allow_input_barcode')
        if setting_check == 'allow':
            list_ma_pin = self.env['res.users'].search([('ma_bin', '!=', False)]).mapped('ma_bin')
            if str(ma_bin) in list_ma_pin:
                return False
            else:
                return True
        else:
            return False

    @api.onchange('ma_bin')
    def _get_check_show_ma_bin(self):
        for record in self:
            if self.env['ir.values'].get_default('purchase.config.settings', 'allow_input_barcode') == 'allow':
                record.check_show_ma_bin = True
                list_ma_pin = self.env['res.users'].search([('ma_bin', '!=', False)]).mapped('ma_bin')
                if record.ma_bin and record.ma_bin in list_ma_pin:
                    record.check_used_ma_bin = True
            else:
                record.check_show_ma_bin = False

    @api.model
    def create(self, vals):
        res = super(purchase_order_inherit, self).create(vals)
        if self.env['ir.values'].get_default('purchase.config.settings', 'allow_input_barcode') == 'allow':
            res.ma_bin = None
            res.check_show_add_line = False
        return res

    @api.multi
    def write(self, vals):
        if self.env['ir.values'].get_default('purchase.config.settings', 'allow_input_barcode') == 'allow':
            vals.update({
                'ma_bin' : '',
                'check_show_add_line' : False,
            })
        res = super(purchase_order_inherit, self).write(vals)
        return res

class PurchaseConfiguration(models.TransientModel):
    _inherit = 'purchase.config.settings'

    allow_input_barcode = fields.Selection([
        ('allow', 'Sử dụng'),
        ('unallow', 'Không sử dụng')
    ], 'Kiểm tra cho phép nhập Barcode',
        default='unallow')

    @api.multi
    def set_allow_input_barcode_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'purchase.config.settings', 'allow_input_barcode', self.allow_input_barcode)