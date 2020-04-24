# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime

class account_guarantee_inherit(models.Model):
    _inherit = 'account.guarantee'

    account_analytic_account_id = fields.Many2one('account.analytic.account', string='Hợp đồng')
    sale_id = fields.Many2one('sale.order', required=False, readonly=True)
    unc_id = fields.Many2one('account.voucher',string="Giấy báo nợ (Chi)")
    unc_count = fields.Integer(string="Giấy báo nợ (Chi)",compute="_get_unc_count")

    @api.multi
    def _get_unc_count(self):
        for rec in self:
            rec.unc_count = len(rec.unc_id)

    @api.model
    def default_get(self, fields):
        res = super(account_guarantee_inherit, self).default_get(fields)
        res['account_analytic_account_id'] = self._context.get('account_analytic_account_id', False)
        return res

    @api.multi
    def action_approve(self):
        for record in self:
            record.state = 'approved'
            account_1121_bank = self.env['account.account'].search([('code','=','1121')],limit=1)
            obj = self.env['account.voucher'].with_context({
                'default_voucher_type': 'purchase',
                'voucher_type': 'purchase',
                'unt_unc': True,
                'default_voucher_type': 'purchase',
                'default_unt_unc': True,
                'default_partner_id': record.partner_id and record.partner_id.id or False,
                'default_bank_id': record.partner_id and record.partner_id.id or False,
            })
            note = "Trả tiền phí bảo lãnh mã %s - dự án %s" % (record.name or '',record.project_id.name)
            data_unc = obj.default_get(obj._fields)
            data_unc.update({
                'bank' : record.partner_id.id,
                'account_id' : account_1121_bank.id,
                'line_ids' : [(0,0,{
                    'name': note,
                    'account_id': record.guarantee_account_id.id,
                    'price_unit': record.guarantee_fee,
                })]
            })
            record.unc_id = obj.create(data_unc)

    @api.multi
    def action_draft(self):
        for record in self:
            record.state = 'draft'
            if record.unc_id:
                if record.unc_id.state == 'posted':
                    record.unc_id.cancel_voucher()
                record.unc_id.unlink()

    @api.multi
    def open_unc(self):
        action_picking = self.env.ref('account_bank_voucher.unc_action_purchase_receipt')
        action = action_picking.read()[0]
        action['domain'] = [('id', 'in', self.unc_id.ids)]
        return action


