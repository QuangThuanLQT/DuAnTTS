# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    @api.model
    def default_get(self, fields):
        res = super(account_voucher, self).default_get(fields)
        if self._context.get('default_payment_journal_id', False):
            res.update({
                'payment_journal_id': self._context.get('default_payment_journal_id'),
            })
        return res

    @api.depends('company_id', 'pay_now', 'account_id')
    def _compute_payment_journal_id(self):
        res = super(account_voucher, self)._compute_payment_journal_id()
        for voucher in self:
            if self._context.get('default_payment_journal_id', False):
                voucher.payment_journal_id = self._context.get('default_payment_journal_id')
                voucher.account_id = voucher.payment_journal_id.default_debit_account_id
        return res

    sms_payment_id = fields.Many2one('tts.sms.inbox')

    @api.model
    def create(self, vals):
        res = super(account_voucher, self).create(vals)
        if res.sms_payment_id:
            data = {
                'account_voucher_id': res.id,
                'create_uid_voucher': self.env.uid,
                'create_date_voucher': datetime.now(),
                'state': 'done',
                'created_voucher': True,
                'customer_id': res.partner_id.id,
                'customer_phone': res.partner_id and res.partner_id.phone,
                'user_id': res.partner_id and res.partner_id.user_id.id,
                'city_id': res.partner_id and res.partner_id.feosco_city_id.id,
            }
            if res.sale_id:
                data.update({
                    'don_hang': res.sale_id,
                })
            res.sms_payment_id.write(data)

        return res

    @api.multi
    def write(self, vals):
        res = super(account_voucher, self).write(vals)
        for record in self:
            if record.sms_payment_id and record.state in ['draft']:
                data = {
                    'customer_id': record.partner_id.id,
                    'customer_phone': record.partner_id and record.partner_id.phone,
                    'user_id': record.partner_id and record.partner_id.user_id.id,
                    'city_id': record.partner_id and record.partner_id.feosco_city_id.id,
                    'don_hang': record.sale_id,
                }
                record.sms_payment_id.write(data)
        return res
