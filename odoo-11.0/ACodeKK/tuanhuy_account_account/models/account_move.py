# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_move(models.Model):
    _inherit = 'account.move'

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        result = super(account_move, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        return result