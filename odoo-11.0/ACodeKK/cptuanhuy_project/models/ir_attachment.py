# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ir_attachment_inherit(models.Model):
    _inherit = 'ir.attachment'

    active = fields.Boolean(default=True,string="Lưu trữ")

    @api.multi
    def toggle_active(self):
        for record in self:
            record.active = not record.active