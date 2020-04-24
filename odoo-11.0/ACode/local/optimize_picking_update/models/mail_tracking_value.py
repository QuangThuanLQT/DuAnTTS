# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mail_tracking_value(models.Model):
    _inherit = 'mail.tracking.value'

    @api.model
    def create(self, values):
        result = super(mail_tracking_value, self).create(values)
        return result

    @api.multi
    def write(self, values):
        result = super(mail_tracking_value, self).write(values)
        return result