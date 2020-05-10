# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    product_code = fields.Char(related='product_id.default_code', string='Mã sản phẩm', store=True)
    reconcile_number = fields.Float(compute="_get_reconcile_number",store=True)
    record_checked = fields.Boolean('Checked')
    debit_amount_residual = fields.Float(compute="_get_debit_credit_residual",store=True)
    credit_amount_residual = fields.Float(compute="_get_debit_credit_residual",store=True)
    account_doiung = fields.Char('Tài Khoản Đối Ứng', compute="get_account_doiung",store=True)

    @api.depends('move_id','debit','credit','move_id.line_ids','account_id')
    def get_account_doiung(self):
        for record in self:
            move_id = record.move_id
            if record.debit > record.credit:
                list = []
                for line in move_id.line_ids:
                    if line.credit > 0 and line.account_id.code not in list:
                        list.append(line.account_id.code)
                doiung = ', '.join(list)

            elif record.debit < record.credit:
                list = []
                for line in move_id.line_ids:
                    if line.debit > 0 and line.account_id.code not in list:
                        list.append(line.account_id.code)
                doiung = ', '.join(list)
            else:
                list = []
                for line in move_id.line_ids.filtered(lambda l: l.account_id.code != record.account_id.code):
                    if line.account_id.code not in list:
                        list.append(line.account_id.code)
                doiung = ', '.join(list)
            record.account_doiung = doiung

    @api.multi
    @api.depends('amount_residual')
    def _get_debit_credit_residual(self):
        for record in self:
            if record.amount_residual == 0:
                record.debit_amount_residual = record.credit_amount_residual = 0.0
            elif record.amount_residual < 0:
                record.credit_amount_residual = -record.amount_residual
                record.debit_amount_residual = 0.0
            else:
                record.credit_amount_residual = 0.0
                record.debit_amount_residual = record.amount_residual

    # @api.multi
    # def _get_debit_credit_residual(self):
    #     partner_id = False
    #     args = False
    #     if self._context.get('args',False):
    #         args = self._context.get('args',False)
    #     if args and any([ 'partner_id' in a for a in args]):
    #         partner = [x for x in args if 'partner_id' in x ]
    #         partner_id = list(partner[0][2])
    #     for record in self:
    #         no_before,co_before = record._get_debit_credit_amount(partner_id)
    #         sum_amount = no_before + record.debit - co_before - record.credit
    #         if sum_amount > 0:
    #             record.debit_amount_residual = sum_amount
    #             record.credit_amount_residual = 0
    #         else:
    #             record.debit_amount_residual = 0
    #             record.credit_amount_residual = -sum_amount
    #
    # @api.model
    # def _get_debit_credit_amount(self,partner_id):
    #     no_before = co_before = 0
    #     no_before_value = co_before_value = 0
    #     if self.date:
    #         query = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                             FROM account_move_line aml
    #                                             WHERE aml.account_id = '%s' AND aml.date < '%s' """ % (
    #             self.account_id.id, self.date)
    #         if partner_id:
    #             query += 'AND aml.partner_id in (%s) '% (', '.join(str(id) for id in partner_id))
    #         self.env.cr.execute(query)
    #         move_before = self.env.cr.fetchall()
    #         if move_before[0] and (move_before[0][0] or move_before[0][1]):
    #             no_before = move_before[0][0]
    #             co_before = move_before[0][1]
    #
    #         query1 = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                                         FROM account_move_line aml
    #                                                         WHERE aml.account_id = '%s' AND aml.date = '%s' AND aml.id < '%s' """ % (
    #             self.account_id.id, self.date,self.id)
    #         if partner_id:
    #             query1 += 'AND aml.partner_id in (%s) '% (', '.join(str(id) for id in partner_id))
    #         self.env.cr.execute(query1)
    #         move_before1 = self.env.cr.fetchall()
    #         if move_before1[0] and (move_before1[0][0] or move_before1[0][1]):
    #             no_before += move_before1[0][0]
    #             co_before += move_before1[0][1]
    #
    #         if (no_before - co_before) > 0:
    #             no_before_value = no_before - co_before
    #             co_before_value = 0
    #         else:
    #             no_before_value = 0
    #             co_before_value = co_before - no_before
    #     return no_before_value,co_before_value

    def action_update_check_record(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        for order in orderlines:
            order.with_context(check_move_validity=False).record_checked = False

    @api.multi
    def change_record_checked(self):
        for record in self:
            if not record.record_checked:
                record.with_context(check_move_validity=False).record_checked = True
            else:
                record.with_context(check_move_validity=False).record_checked = False

    @api.multi
    @api.depends('debit','credit')
    def _get_reconcile_number(self):
        for record in self:
            record.reconcile_number = record.debit - record.credit

    @api.model
    def create(self, values):
        record = super(account_move_line, self).create(values)
        return record