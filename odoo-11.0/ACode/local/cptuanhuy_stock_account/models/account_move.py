# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, values):
        record = super(AccountMove, self).create(values)
        return record

    @api.multi
    def write(self, values):
        result = super(AccountMove, self).write(values)
        return result

    @api.multi
    def post(self):
        res = super(AccountMove, self).post()
        if self._context.get('force_set_date_by_picking',False):
            self.write({'date': self._context.get('force_set_date_by_picking',False)})
        return res