# -*- coding: utf-8 -*-

from odoo import models, fields, api


class invoices(models.Model):
    _inherit = 'account.invoice'

    journal_id = fields.Many2one('account.journal', string='Journal', required=True, states={'confirm': [('readonly', True)]})
    account_id = fields.Many2one('account.account', string='Account')
    date_order = fields.Date('Order Date')
    date_dues = fields.Date(string='Due Date',
                           readonly=True, states={'draft': [('readonly', False)]}, index=True, copy=False,
                           help="If you use payment terms, the due date will be computed automatically at the generation "
                                "of accounting entries. The Payment terms may compute several due dates, for example 50% "
                                "now and 50% in one month, but if you want to force a due date, make sure that the payment "
                                "term is not set on the invoice. If you keep the Payment terms and the due date empty, it "
                                "means direct payment.")
    move_id = fields.Many2one('account.move', string='Journal Entry',
                              readonly=True, index=True, ondelete='restrict', copy=False,
                              help="Link to the automatically generated Journal Items.")
    origin = fields.Char(string='Source Document')

    tax_line_ids = fields.One2many('account.invoice.tax', 'invoice_id', string='Tax Lines', oldname='tax_line',
                                   readonly=True, states={'draft': [('readonly', False)]}, copy=True)
