# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from collections import defaultdict


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def create(self, values):
        result = super(StockQuant, self).create(values)
        return result

    @api.multi
    def write(self, values):
        result = super(StockQuant, self).write(values)
        return result

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        if 'purchase_order_return' in self._context and self._context['purchase_order_return'] == True:
            data = move.picking_id.purchase_id.date_order
            self = self.with_context(force_period_date=data)
        elif 'sale_order_return' in self._context and self._context['sale_order_return'] == True:
            data = move.sale_order_id.date_order
            self = self.with_context(force_period_date=data)
        if 'active_id' in self._context and 'active_model' in self._context:
            if self._context['active_model'] in ['sale.order', 'purchase.order']:
                order = self.env[self._context['active_model']].browse(self._context['active_id'])
                self = self.with_context(force_period_date=order.date_order)
        else:
            if move.picking_id:
                date_order = move.picking_id and move.picking_id.purchase_id and move.picking_id.purchase_id.date_order or move.picking_id and move.picking_id.sale_id and move.picking_id.sale_id.date_order or False
                if date_order:
                    # date_order = fields.Date.context_today(self)
                    self = self.with_context(force_period_date=date_order)
        result = super(StockQuant, self)._create_account_move_line(move, credit_account_id, debit_account_id,
                                                                   journal_id)
        return result

    # def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
    #     super(StockQuant, self.with_context({
    #         'force_period_date': move.date_expected or fields.Date.today()
    #     }))._create_account_move_line(move, credit_account_id, debit_account_id, journal_id)

    def get_account_for_move(self, move):

        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if 'update_account_move_wh_in' in self._context:
            journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
            self._get_account_move_line(move, acc_src, acc_valuation,
                                        journal_id, move.picking_id.name)

        # Create Journal Entry for products leaving the company
        if 'update_account_move_wh_out' in self._context:
            journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
            self._get_account_move_line(move, acc_valuation, acc_dest,
                                        journal_id, move.picking_id.name)

    def _get_account_move_line(self, move, credit_account_id, debit_account_id, journal_id, picking_name):
        # group quants by cost
        quant_cost_qty = defaultdict(lambda: 0.0)
        for quant in self:
            quant_cost_qty[quant.cost] += quant.qty

        account_move_ids = self.env['account.move.line'].search([
            ('ref', '=', picking_name),
            ('product_id', '=', move.product_id.id)
        ]).mapped('move_id')
        if len(account_move_ids) == 1:
            total = 0
            move_line_changed = self.env['account.move.line']
            for cost, qty in quant_cost_qty.iteritems():
                move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
                for move_line in move_lines:
                    move_line = move_line[2]
                    move_line_need_change = (account_move_ids.line_ids - move_line_changed).filtered(
                        lambda ml: ml.account_id.id == move_line.get('account_id', False))
                    if move_line_need_change:
                        move_line_changed += move_line_need_change
                        self._cr.execute("""UPDATE account_move_line SET credit=%s, debit=%s WHERE id=%s""" % (
                            move_line.get('credit', 0) or 0,
                            move_line.get('debit', 0) or 0,
                            move_line_need_change.id
                        ))
                        self._cr.commit()
                    else:
                        break
                    total += move_line.get('debit', 0)
            if total:
                self._cr.execute("""UPDATE account_move SET amount=%s WHERE id=%s""" % (total, account_move_ids.id))
                self._cr.commit()

        if len(account_move_ids) > 1:
            move_changed = self.env['account.move']
            if len(quant_cost_qty) == len(account_move_ids):
                for cost, qty in quant_cost_qty.iteritems():
                    total = 0
                    move_line_changed = self.env['account.move.line']
                    for acc_move in (account_move_ids - move_changed):
                        move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
                        for move_line in move_lines:
                            move_line = move_line[2]
                            move_line_need_change = (acc_move.line_ids - move_line_changed).filtered(
                                lambda ml: ml.account_id.id == move_line.get('account_id', False))
                            if move_line_need_change:
                                move_line_changed += move_line_need_change
                                self._cr.execute("""UPDATE account_move_line SET credit=%s, debit=%s WHERE id=%s""" % (
                                    move_line.get('credit', 0) or 0,
                                    move_line.get('debit', 0) or 0,
                                    move_line_need_change.id))
                                self._cr.commit()
                            else:
                                break
                            total += move_line.get('debit', 0)

                        if total:
                            self._cr.execute("""UPDATE account_move SET amount=%s WHERE id=%s""" % (total, acc_move.id))
                            self._cr.commit()
                        move_changed += acc_move
                        break
