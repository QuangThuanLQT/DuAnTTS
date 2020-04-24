# -*- coding: utf-8 -*-

from odoo import models, fields, api


class bank_estimate(models.Model):
    _name = 'bank.estimate'

    name           = fields.Char('Name', related='asset_id.name')
    partner_id     = fields.Many2one('res.partner', 'Bank')
    asset_id       = fields.Many2one('account.asset.asset', 'Asset')
    asset_value    = fields.Float('Asset Value', related='asset_id.value_residual')
    estimate_value = fields.Float('Estimate Value')
    date           = fields.Date('Date', default=lambda self: fields.Date.today())
    asset_code     = fields.Char('Asset Code')
    estimate_date  = fields.Date('Estimate Date')
    payment_state  = fields.Selection([('on_time', 'Đúng hạn'),
                                      ('late', 'Quá hạn')], string='Payment Status')
    line_ids       = fields.One2many('bank.estimate.line', 'bank_estimate_id')
    state          = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('progress', 'In Progress'),
        ('hold', 'Hold'),
        ('cancelled', 'Cancelled'),
    ], 'Status', default='draft')


    mortgage_value = fields.Float('Giá trị tài sản đã thế chấp',compute='get_mortgage_value')
    remaind_value = fields.Float('Giá trị tài sản còn lại', compute='get_remaind_value')


    @api.multi
    def get_mortgage_value(self):
        for record in self:
            value_ids = self.env['account.asset.value'].search([('asset_id', '=', record.id), ('loan_id.state', 'in', ['posted', 'closed'])])
            value_id = self.env['account.asset.value'].search([('asset_id', '=', record.id), ('account_guarantee_id.state', 'in', ['requested', 'done'])])
            value = 0
            for line in value_ids:
                value += line.amount
            for line in value_id:
                value += line.amount
            record.mortgage_value = value

    @api.depends('mortgage_value', 'estimate_value',)
    def get_remaind_value(self):
        for r in self:
            if not r.mortgage_value or not r.estimate_value:
                r.remaind_value = 0.0
            else:
                r.remaind_value = r.estimate_value - r.mortgage_value

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_hold(self):
        self.state = 'hold'

    @api.multi
    def action_cancel(self):
        self.state = 'cancelled'


class bank_estimate_line(models.Model):
    _name = 'bank.estimate.line'

    bank_estimate_id = fields.Many2one('bank.estimate')
    code = fields.Char('Code')
    partner_id = fields.Many2one('res.partner', 'Bank')
    date = fields.Date('Date')
    amount = fields.Float('Amount')
    state = fields.Selection([
        ('done', 'Done'),
        ('progress', 'In Progress'),
    ], string='State')
