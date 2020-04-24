# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, values):
        result = super(account_move_line, self).create(values)
        return result

    @api.multi
    def write(self, values):
        result = super(account_move_line, self).write(values)
        return result