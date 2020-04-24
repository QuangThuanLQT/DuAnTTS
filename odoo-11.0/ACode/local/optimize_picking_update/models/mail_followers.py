# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mail_followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def create(self, values):
        if values.get('res_model', False) == 'stock.picking':
            result = None
        else:
            result = super(mail_followers, self).create(values)
        return result

    @api.multi
    def write(self, values):
        result = super(mail_followers, self).write(values)
        return result