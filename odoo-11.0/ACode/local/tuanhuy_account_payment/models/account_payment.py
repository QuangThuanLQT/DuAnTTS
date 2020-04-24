# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class account_payment(models.Model):
    _inherit = 'account.payment'

    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type', required=True)

    original_documents = fields.Char('Original documents')
    # date_original_documents = fields.Date(string="Date")
    old_debt   = fields.Float(string='Old Debt', digits=(12, 2))
    old_residual = fields.Float(string='Old Residual', digits=(12, 2))
    account_payment_line_so = fields.One2many('account.payment.line.so','account_payment_id')
    # account_payment_line_po = fields.One2many('account.payment.line.po', 'account_payment_id')
    account_move_ids = fields.Many2many('account.move.line')
    account_move_ids_debt = fields.Char()
    amount_payment_remaining = fields.Float(string='Excess cash', digits=(12, 2),compute="_get_amount_payment_remaining")
    amount_payment_shortage  = fields.Float(string='Money shortage', digits=(12, 2),compute="_get_amount_payment_remaining")

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount >= 0.0:
            raise ValidationError(_('The payment amount must be strictly positive.'))

    # @api.onchange('partner_id')
    # def _get_old_debt(self):
    #     for record in self:
    #         account_move_line_ids = self.env['account.move.line'].search([('move_id.state','=','posted'),('partner_id','=',record.partner_id.id),('account_id.code','=','131')])
    #         sale_order_ids = self.env['sale.order'].search(
    #             [('partner_id', '=', record.partner_id.id), ('invoice_status', '=', 'invoiced')]).filtered(
    #             lambda so: 'paid' not in so.mapped('invoice_ids').mapped('state'))
    #         invoice_amount_residual = sum(sale_order_ids.mapped('invoice_ids').mapped('residual'))
    #         amount_total = sum(account_move_line_ids.mapped('debit')) - sum(account_move_line_ids.mapped('credit')) - invoice_amount_residual
    #         if amount_total > 0:
    #             record.old_debt = amount_total
    #             record.old_residual = 0
    #         else:
    #             record.old_debt = 0
    #             record.old_residual = -amount_total

    @api.onchange('payment_type','partner_type')
    def onchange_payment_type_partner_type(self):
        self.onchange_partner_id_for_so()



    @api.onchange('partner_id')
    def onchange_partner_id_for_so(self):
        if not self.partner_id:
            self.account_payment_line_so = None
        else:
            sale_order_ids = self.env['sale.order']
            # TODO THANH TOAN BAN HANG
            account_payment_line_so = []
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                sale_order_ids = self.env['sale.order'].search(
                    [('sale_order_return','=',False),('partner_id', '=', self.partner_id.id), ('invoice_status', '=', 'invoiced')]).filtered(
                    lambda so: 'paid' not in so.mapped('invoice_ids').mapped('state'))
                account_payment_line_so = []
                sequence = 1

                domain = [('account_id.code', '=', '131'), ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id), ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                lines = self.env['account.move.line'].search(domain).filtered(lambda aml: '5213' not in aml.move_id.mapped('line_ids').mapped('account_id').mapped('code'))
                self.old_residual = -sum(lines.mapped('amount_residual')) or 0.0

                domain1 = [('account_id.code', '=', '131'),
                           ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                           ('reconciled', '=', False), ('journal_id.type', '!=', 'sale')]
                domain1.extend([('credit', '=', 0), ('debit', '>', 0)])
                lines1 = self.env['account.move.line'].search(domain1).filtered(lambda aml: '4111' in aml.move_id.mapped('line_ids').mapped('account_id').mapped('code'))

                self.old_debt = sum(lines1.mapped('amount_residual')) or 0.0


                amount_payment_remaining = self.old_residual - self.old_debt

            # TODO THANH TOAN TRA HANG BAN
            if self.payment_type == 'outbound' and self.partner_type == 'customer':
                sale_order_ids = self.env['sale.order'].search(
                    [('sale_order_return','=',True),('partner_id', '=', self.partner_id.id)]).filtered(
                    lambda so: 'paid' not in so.mapped('invoice_ids').mapped('state'))
                account_payment_line_so = []
                sequence = 1

                domain = [('account_id.code', '=', '131'), ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id), ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                lines = self.env['account.move.line'].search(domain).filtered(lambda aml: '5111' not in aml.move_id.mapped('line_ids').mapped('account_id').mapped('code'))
                self.old_residual = sum(lines.mapped('amount_residual')) or 0.0

                amount_payment_remaining = self.old_residual - self.old_debt

            for sale_order_id in sale_order_ids.sorted('date_order', reverse=False):
                amount_remaining = sum(sale_order_id.mapped('invoice_ids').mapped('residual'))
                amount_payment = 0
                if amount_payment_remaining > 0:
                    if (amount_payment_remaining - amount_remaining) > 0:
                        amount_payment = amount_remaining
                    else:
                        amount_payment = amount_payment_remaining
                    amount_payment_remaining -= amount_payment
                account_payment_line_so.append((0, 0, {
                    'sale_order_id': sale_order_id.id,
                    'sequence': sequence,
                    # 'amount_sale_order': sale_order_id.amount_total,
                    'amount_remaining': amount_remaining,
                    'amount_payment': amount_payment,
                    'check_payment': True,
                    'order_date' : sale_order_id.date_order,
                }))
                sequence += 1
            self.account_payment_line_so = None
            self.account_payment_line_so = account_payment_line_so



    @api.onchange('account_payment_line_so','amount','partner_id','old_debt','old_residual')
    def _get_amount_payment_remaining(self):
        amount_payment_remaining = self.amount - self.old_debt + self.old_residual - sum(self.account_payment_line_so.filtered(lambda l: l.check_payment).mapped('amount_remaining'))
        if amount_payment_remaining > 0:
            self.amount_payment_remaining = amount_payment_remaining
            self.amount_payment_shortage = 0
        else:
            self.amount_payment_remaining = 0
            self.amount_payment_shortage = - amount_payment_remaining

    @api.multi
    def action_multi_post_new(self):
        for record in self:
            # record._get_old_debt()
            record.onchange_partner_id_for_so()
            record.action_post_new()



    @api.multi
    def action_post_new(self):
        for record in self:
            # TODO THANH TOAN BAN HANG
            if record.payment_type == 'inbound' and self.partner_type == 'customer':
                domain = [('account_id.code', '=', '131'),
                          ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                          ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                account_move_ids = self.env['account.move.line'].search(domain).filtered(
                    lambda aml: '5213' not in aml.move_id.mapped('line_ids').mapped('account_id').mapped('code'))

                domain1 = [('account_id.code', '=', '131'),
                           ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                           ('reconciled', '=', False), ('journal_id.type', '!=', 'sale')]
                domain1.extend([('credit', '=', 0), ('debit', '>', 0)])
                account_move_ids_debt = self.env['account.move.line'].search(domain1).filtered(
                    lambda aml: '4111' in aml.move_id.mapped('line_ids').mapped('account_id').mapped('code') and aml.amount_residual <= self.old_debt)

                for move_residual in account_move_ids.sorted('date', reverse=False):
                    for move_debt in account_move_ids_debt.sorted('date', reverse=False):
                        if move_debt.reconciled:
                            continue
                        else:
                            (move_residual + move_debt).reconcile(False,False)
                        if not move_residual.amount_residual:
                            break

                for move_residual in account_move_ids.filtered(lambda m: not m.reconciled).sorted('date', reverse=False):
                    for account_payment_line in record.account_payment_line_so.filtered(lambda x: x.check_payment):
                        for invoice in account_payment_line.mapped('sale_order_id').mapped('invoice_ids'):
                            if move_residual.reconciled:
                                break
                            if invoice.move_id:
                                invoice.assign_outstanding_credit(move_residual.id)

            # TODO THANH TOAN TRA HANG BAN
            if record.payment_type == 'outbound' and self.partner_type == 'customer':
                domain = [('account_id.code', '=', '131'),
                          ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                          ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                account_move_ids = self.env['account.move.line'].search(domain).filtered(
                    lambda aml: '5111' not in aml.move_id.mapped('line_ids').mapped('account_id').mapped('code'))

                for move_residual in account_move_ids.filtered(lambda m: not m.reconciled).sorted('date', reverse=False):
                    for account_payment_line in record.account_payment_line_so.filtered(lambda x: x.check_payment):
                        for invoice in account_payment_line.mapped('sale_order_id').mapped('invoice_ids'):
                            if move_residual.reconciled:
                                break
                            if invoice.move_id:
                                invoice.assign_outstanding_credit(move_residual.id)

        self.state = 'reconciled'



    # @api.onchange('account_payment_line_so')
    # def onchange_account_payment_line_so(self):
    #     amount_payment_remaining = self.amount - self.old_debt
    #     for line in self.account_payment_line_so:
    #         if not line.check_payment:
    #             line.write({
    #                 'amount_payment' : 0
    #             })
    #     for line in self.account_payment_line_so.filtered(lambda l: l.check_payment).sorted('sequence', reverse=False):
    #         amount_remaining = line.amount_remaining
    #         amount_payment = 0
    #         if amount_payment_remaining > 0:
    #             if (amount_payment_remaining - amount_remaining) > 0:
    #                 amount_payment = amount_remaining
    #             else:
    #                 amount_payment = amount_payment_remaining
    #             amount_payment_remaining -= amount_payment
    #         line.write({
    #             'amount_payment': amount_payment
    #         })

    # @api.onchange('amount','old_debt','account_payment_line_so')
    # def onchange_amount_old_debt_line(self):
    #     amount_payment_remaining = self.amount - self.old_debt + self.old_residual
    #     for line in self.account_payment_line_so:
    #         if not line.check_payment:
    #             line.write({
    #                 'amount_payment': 0
    #             })
    #             line.amount_payment = 0
    #     for line in self.account_payment_line_so.filtered(lambda l: l.check_payment).sorted('sequence', reverse=False):
    #         amount_remaining = line.amount_remaining
    #         amount_payment = 0
    #         if amount_payment_remaining > 0:
    #             if (amount_payment_remaining - amount_remaining) > 0:
    #                 amount_payment = amount_remaining
    #             else:
    #                 amount_payment = amount_payment_remaining
    #             amount_payment_remaining -= amount_payment
    #         line.write({
    #             'amount_payment': amount_payment
    #         })
    #         line.amount_payment = amount_payment

    @api.onchange('original_documents')
    def onchange_original_documents(self):
        if self.original_documents:
            original_documents = self.search([('original_documents', '=', self.original_documents)])
            if original_documents:
                warning = {
                    'title': _("Warning"),
                    'message': "Unfortunately this original documents is already used, please choose a unique one"
                }
                return {'warning': warning}
                # raise UserError(_("Unfortunately this original documents is already used, please choose a unique one"))
            else:
                journal_id = self.env['account.journal'].search(
                    [('type', 'in', ['cash']), ('at_least_one_outbound', '=', True), ('name', '=', 'Cash')])
                if journal_id:
                    self.journal_id = journal_id[0].id

class account_payment_line_so(models.Model):
    _name = 'account.payment.line.so'

    sequence = fields.Integer(string="Sequence")
    sale_order_id = fields.Many2one('sale.order',string="Sale Order")
    order_date = fields.Date()
    amount_sale_order = fields.Float('Amount Total',digits=(12, 2))
    amount_remaining = fields.Float('Amount Remaining', digits=(12, 2))
    amount_payment = fields.Float('Amount Payment', digits=(12, 2))
    check_payment = fields.Boolean(string="Payment")
    account_payment_id = fields.Many2one('account.payment')


# class account_payment_line_po(models.Model):
#     _name = 'account.payment.line.po'
#
#     sequence = fields.Integer(string="Sequence")
#     purchase_order_id = fields.Many2one('purchase.order',string="Purchase Order")
#     amount_sale_order = fields.Float('Amount Total',digits=(12, 2))
#     amount_remaining = fields.Float('Amount Remaining', digits=(12, 2))
#     amount_payment = fields.Float('Amount Payment', digits=(12, 2))
#     check_payment = fields.Boolean(string="Payment")
#     account_payment_id = fields.Many2one('account.payment')