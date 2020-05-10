# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class account_guarantee(models.Model):
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name = 'account.guarantee'

    def _default_company(self):
        force_company = self._context.get('force_company')
        if not force_company:
            return self.env.user.company_id.id
        return force_company

    def _default_type(self):
        force_type = self._context.get('force_type')
        if not force_type:
            return self.env['account.guarantee.type'].search([], limit=1).id
        return force_type

    name = fields.Char(
        copy=False,
        required=True,
        readonly=True,
        default='/',
        states={'draft': [('readonly', False)]},
    )
    code = fields.Char(
        copy=False,
        required=False,
        readonly=False,
        default='',
        states={'draft': [('readonly', False)]},
    )
    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        string='Guaranter',
        help='Company or individual that lends the money at an interest rate.',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=_default_company,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        # ('bank_approved', 'Bank Approved'),
        # ('draft_letter', 'Draft Letter'),
        # ('validated_letter', 'Validated Letter'),
        ('done', 'Done'),
    ], required=True, copy=False, default='draft')
    start_date = fields.Date(
        help='Start of the moves',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    end_date = fields.Date(
        help='End of the moves',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    sale_id = fields.Many2one(
        'sale.order',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    guarantee_amount = fields.Monetary(
        currency_field='currency_id',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    guarantee_fee = fields.Monetary(
        currency_field='currency_id',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    guarantee_fund = fields.Monetary(
        currency_field='currency_id',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    guarantee_credit = fields.Monetary(
        currency_field='currency_id',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    guarantee_type_id = fields.Many2one(
        'account.guarantee.type',
        required=True,
        default=_default_type,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    journal_id = fields.Many2one(
        'account.journal',
        domain="[('company_id', '=', company_id)]",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    guarantee_account_id = fields.Many2one(
        'account.account',
        domain="[('company_id', '=', company_id)]",
        string='Guarantee account',
        help='Account that will contain the fee amount',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_currency',
        readonly=True,
    )
    job_costing_id = fields.Many2one('job.costing', 'Báo giá')
    account_asset_id = fields.Many2one('account.asset.asset', string='Tài sản đảm bảo')
    asset_guaranteed = fields.Float(string='Đảm bảo bằng TSĐB')
    beneficiary_id = fields.Char(string='Người thụ hưởng')
    move_id = fields.Many2one('account.move', string='Bút toán sổ nhật ký')
    # guaranteed_total = fields.Float(string='Tổng đảm bảo', compute='_compute_guaranteed_total')

    # @api.multi
    # def _compute_guaranteed_total(self):
    #     for record in self:
    #         guaranteed_total        = record.guarantee_fund + record.guarantee_credit + record.asset_guaranteed
    #         record.guaranteed_total = guaranteed_total

    @api.model
    def default_get(self, fields):
        res = super(account_guarantee, self).default_get(fields)
        res['journal_id'] = self.env.ref('stable_hr_timesheet_invoice.expense_journal').id
        res['guarantee_account_id'] = self.env.ref('l10n_vn.1_chart6428').id
        return res

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_requrest(self):
        self.state = 'requested'

    @api.multi
    def action_approve(self):
        self.state = 'approved'

    @api.multi
    def action_bank_approve(self):
        self.state = 'bank_approved'

    @api.multi
    def action_draft_letter(self):
        self.state = 'draft_letter'

    @api.multi
    def action_validate_letter(self):
        self.state = 'validated_letter'

    @api.multi
    def action_done(self):
        # debit_line_vals = {
        #     'name': self.name,
        #     'ref': self.name,
        #     'partner_id': self.partner_id and self.partner_id.id,
        #     'debit': self.guarantee_amount,
        #     'credit': 0,
        #     'account_id': self.guarantee_account_id and self.guarantee_account_id.id or False,
        # }
        #
        # credit_account_id = self.partner_id.bank_account_id
        # if not credit_account_id:
        #     credit_account_id = self.env['account.account'].search([('code', '=', '1121'),], limit=1)
        # credit_line_vals = {
        #     'name': self.name,
        #     'ref': self.name,
        #     'partner_id': self.partner_id and self.partner_id.id,
        #     'credit': self.guarantee_amount,
        #     'debit': 0,
        #     'account_id': credit_account_id.id,
        # }
        # line_ids = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        # move_data = {
        #     'journal_id': self.journal_id and self.journal_id.id or False,
        #     'date': datetime.now().strftime('%Y-%m-%d'),
        #     'ref': self.name or '',
        #     'line_ids': line_ids,
        # }
        # move = self.env['account.move'].create(move_data)
        # move.post()
        # self.move_id = move
        self.state = 'done'

    @api.depends('journal_id', 'company_id')
    def _compute_currency(self):
        for rec in self:
            rec.currency_id = (rec.journal_id.currency_id or rec.company_id.currency_id)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.get_default_name(vals)
        return super(account_guarantee, self).create(vals)

    def get_default_name(self, vals):
        return self.env['ir.sequence'].next_by_code('account.guarantee') or '/'