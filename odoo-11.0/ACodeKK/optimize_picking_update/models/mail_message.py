# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mail_message(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        if values.get('model', False) in ['stock.picking', 'procurement.order']:
            result = None
        else:
            result = super(mail_message, self).create(values)
        return result

    @api.multi
    def write(self, values):
        result = super(mail_message, self).write(values)
        return result