# -*- coding: utf-8 -*-

from odoo import models, fields, api

# Overrite Odoo translation model
class IrTranslation(models.Model):
    _inherit = 'ir.translation'

    @api.model
    def _get_import_cursor(self):
        return super(IrTranslation, self.with_context({
            'overwrite': True
        }))._get_import_cursor()
