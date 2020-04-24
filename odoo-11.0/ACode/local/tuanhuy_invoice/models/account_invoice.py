# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError

class tuanhuy_invoice(models.Model):
    _inherit = 'account.invoice'

    has_co            = fields.Boolean('CO')
    has_cq            = fields.Boolean('CQ')
    has_stock_receipt = fields.Boolean('Stock Receipt')
    invoice_date_real = fields.Date('Invoice Date Real')
    invoice_total_real = fields.Float('Giá Trị Hoá Đơn Thực')
    invoice_number_real = fields.Char('Invoice Number Real')
    date_order = fields.Date('Order Date')
    number_origin = fields.Char('Number Origin')
    record_checked = fields.Boolean('Done')

    @api.multi
    def change_record_checked(self):
        for record in self:
            if not record.record_checked:
                record.record_checked = True
            else:
                record.record_checked = False

    @api.multi
    def action_invoice_open(self):
        res = super(tuanhuy_invoice, self).action_invoice_open()
        for record in self:
            if 'from_cptuanhuy' not in self._context:
                record.date_invoice = record.date_order or fields.Date.context_today(self)
            if record.move_id:
                record.move_id.ref = record.origin
        return res

    def action_update_check_record(self):
        ids = self.env.context.get('active_ids', [])
        invoicelines = self.browse(ids)
        for invoice in invoicelines:
            invoice.record_checked = False

    @api.multi
    def action_cancel_invoice(self):
        for invoice in self:
            if invoice.state not in ['paid', 'cancel']:
                if invoice.move_id:
                    self._cr.execute("""DELETE FROM account_move_line WHERE move_id=%s""" % (invoice.move_id.id))
                    self._cr.execute("""UPDATE account_invoice SET move_id=NULL WHERE id=%s""" % (invoice.id))
                    self._cr.execute("""DELETE FROM account_move WHERE id=%s""" % (invoice.move_id.id))

            if invoice.state == 'paid':
                for payment in invoice.payment_ids:
                    self._cr.execute("""DELETE FROM account_payment WHERE id=%s""" % (payment.id))
                payment_move_ids = []
                payment_line_move_ids = []
                for payment_move_line_id in invoice.payment_move_line_ids:
                    if payment_move_line_id.move_id.id not in payment_move_ids:
                        payment_move_ids.append(payment_move_line_id.move_id.id)
                        for line_move in payment_move_line_id.move_id.line_ids.ids:
                            payment_line_move_ids.append(line_move)
                account_partial_reconcile_ids = self.env['account.partial.reconcile'].search(
                    ['|', ('debit_move_id', 'in', payment_line_move_ids),
                     ('credit_move_id', 'in', payment_line_move_ids)])
                account_partial_reconcile_ids.unlink()
                for move_id in payment_move_ids:
                    self._cr.execute("""DELETE FROM account_move_line WHERE move_id = %s""" % (move_id))
                    self._cr.execute("""DELETE FROM account_move WHERE id = %s""" % (move_id))
                if invoice.move_id:
                    self._cr.execute("""DELETE FROM account_move_line WHERE move_id=%s""" % (invoice.move_id.id))
                    self._cr.execute("""UPDATE account_invoice SET move_id=NULL WHERE id=%s""" % (invoice.id))
                    self._cr.execute("""DELETE FROM account_move WHERE id=%s""" % (invoice.move_id.id))

            self._cr.execute("""UPDATE account_invoice SET state='cancel' WHERE id=%s""" % (invoice.id))

    def multi_action_cancel_invoice(self):
        ids = self.env.context.get('active_ids', [])
        invoicelines = self.browse(ids)
        invoicelines.action_cancel_invoice()

    def unpayment_invoice(self):
        ids = self.env.context.get('active_ids', [])
        invoicelines = self.browse(ids)
        for invoice in invoicelines:
            if invoice.payment_move_line_ids:
                for payment in invoice.payment_move_line_ids:
                    payment.with_context(invoice_id=invoice.id).remove_move_reconcile()

    @api.model
    def get_move_line_from_inv(self):
        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = \
                inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total,
                                                                                                            inv.date_invoice)[
                    0]
                res_amount_currency = total_currency
                ctx['date'] = inv._get_currency_rate_date()
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

        return line


    # @api.model
    # def create(self, vals):
    #     result = super(tuanhuy_invoice, self).create(vals)
    #     if result.amount_total == 0 :
    #         raise UserError(_('Không thể tạo hoá đơn giá trị 0.'))
    #     return result

class tuanhuy_account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    discount = fields.Float(digits=(16, 2))

