# -*- coding: utf-8 -*-

from odoo import models, fields, api

class inventory_package_size(models.Model):
    _name = "inventory.package.size"

    number_sign = fields.Float(string='Number Sign')
    name = fields.Char(required=True)
    active = fields.Boolean(default=True, string="Active")

    @api.multi
    def toggle_active(self):
        for rec in self:
            rec.active = not rec.active