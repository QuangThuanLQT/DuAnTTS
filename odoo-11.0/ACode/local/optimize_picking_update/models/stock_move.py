# -*- coding: utf-8 -*-

from odoo import models, fields, api

class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.model
    def create(self, values):
        context = self.env.context.copy() or {}
        context.update({
            'mail_notrack': True,
            'tracking_disable': True
        })
        result = super(stock_move, self.with_context(context)).create(values)
        return result

    @api.multi
    def write(self, values):
        context = self.env.context.copy() or {}
        context.update({
            'mail_notrack': True,
            'tracking_disable': True
        })
        result = super(stock_move, self.with_context(context)).write(values)
        return result

    @api.multi
    def get_price_unit(self):
        return super(stock_move, self).get_price_unit()

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        result = []
        if not self.env.context.get('skip_account_move_line', False):
            result = super(stock_move, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        return result