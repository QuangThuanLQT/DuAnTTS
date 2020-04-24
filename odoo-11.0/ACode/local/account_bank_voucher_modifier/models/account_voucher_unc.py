# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api

class account_voucher_unc(models.Model):
    _name = 'account.voucher.unc'

    def _default_journal_id(self):
        account_1121_bank = self.env['account.journal'].search([('code', '=', 'BNK1')], limit=1)
        return account_1121_bank

    state              = fields.Selection(
        [
            ('draft', 'Bản phác thảo'),
            ('done', 'Hoàn thành'),
            ('cancel', 'Huỷ')
        ],
        string='Trạng thái',
        default='draft'
    )
    ref                = fields.Char('Tham chiếu')
    partner_id         = fields.Many2one('res.partner', string='Người nhận', domain="[('bank','!=',True)]")
    sender_id          = fields.Many2one('res.partner', string='Ngân hàng gửi', domain="[('bank','=',True),('bank_type', '=', 'internal')]")
    bank_id            = fields.Many2one('res.partner', string='Ngân hàng nhận',domain="[('bank','=',True), ('parent_id', '=', False)]")
    amount             = fields.Float(string='Số tiền')
    fees               = fields.Float(string='Phí')
    date_unc           = fields.Date(string='Ngày tạo')
    acc_pay_id         = fields.Many2one('account.payment', required=False, ondelete='cascade', index=True, copy=False)
    acc_inv_id         = fields.Many2one('account.invoice', required=False, ondelete='cascade', index=True, copy=False)
    date_create        = fields.Date('Ngày tạo', default=fields.Date.context_today)
    journal_id         = fields.Many2one('account.journal', string='Sổ kế toán',default=_default_journal_id)
    account_id         = fields.Many2one('account.account', string='Tài khoản')
    record_checked     = fields.Boolean('Done')
    move_id            = fields.Many2one('account.move', string='Bút toán')
    company_id         = fields.Many2one('res.company', default=1)
    acc_number         = fields.Char('Số tài khoản')
    note               = fields.Char(string='Diễn giải', default="Chi")
    account_voucher_id = fields.Many2one('account.voucher',string="Phiếu Chi")
    check_bank_id      = fields.Boolean(compute='_get_check_sender_id')
    sale_id            = fields.Many2one('sale.order', string='Đơn hàng')
    purchase_id        = fields.Many2one('purchase.order', string='Đơn Mua hàng')

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.account_voucher_id:
                rec.account_voucher_id.cancel_voucher()
                rec.account_voucher_id.unlink()
        return super(account_voucher_unc, self).unlink()

    @api.model
    def default_get(self, fields):
        res = super(account_voucher_unc, self).default_get(fields)

        journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
        ], limit=1)
        if journal and journal.id:
            res['journal_id'] = journal.id

        account = self.env['account.account'].search([
            ('code', '=', '331'),
        ], limit=1)
        if account and account.id:
            res['account_id'] = account.id

        return res

    @api.onchange('sender_id')
    def _get_check_sender_id(self):
        ab_bank = self.env.ref('cptuanhuy_accounting.partner_bank_anbinh_cndanang')
        tp_bank = self.env.ref('cptuanhuy_accounting.partner_bank_tienphong_cndanang')
        tc_bank = self.env.ref('cptuanhuy_accounting.partner_bank_teckcom_cndanang')
        domain = [ab_bank.id, tp_bank.id, tc_bank.id]
        if self.sender_id.id in domain:
            self.check_bank_id = True
        else:
            self.check_bank_id = False

    def print_unc(self):
        if self.account_voucher_id:
            return self.account_voucher_id.print_unc_bank()

    @api.multi
    def change_record_checked(self):
        for record in self:
            if not record.record_checked:
                record.record_checked = True
            else:
                record.record_checked = False

    def update_check_account_payment_unc(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        for order in orderlines:
            order.record_checked = False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            bank_ids = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)])
            bank_ids = bank_ids.mapped('bank_partner_id').ids
            return {'domain': {'bank_id': [('id','in',bank_ids)]}}

    @api.onchange('partner_id', 'bank_id')
    def onchange_partner_bank(self):
        if self.partner_id and self.bank_id:
            bank_ids = self.env['res.partner.bank'].search(
                [('partner_id', '=', self.partner_id.id), ('bank_partner_id', '=', self.bank_id.id)])
            if bank_ids and len(bank_ids) == 1:
                self.acc_number = bank_ids.acc_number

    @api.multi
    def change_status_unc(self):
        for rec in self:
            if rec.state == 'draft':
                account_1121_bank = self.env['account.account'].search([('code', '=', '1121')], limit=1)
                obj = self.env['account.voucher'].with_context({
                    'default_voucher_type' : 'purchase',
                    'voucher_type'         : 'purchase',
                    'unt_unc'              : True,
                    'default_voucher_type' : 'purchase',
                    'default_unt_unc'      : True,
                    'default_sale_id'      : rec.sale_id and [(6,0,rec.sale_id.ids)] or False,
                    'default_partner_id'   : rec.partner_id and rec.partner_id.id or False,
                    'default_bank_id'      : rec.partner_id and rec.partner_id.id or False,
                })
                data_unc = obj.default_get(obj._fields)
                line_ids = []
                if rec.amount != 0:
                    line_ids.append((0, 0, {
                        'name': rec.note,
                        'account_id': rec.account_id.id,
                        'price_unit': rec.amount,
                    }))
                if rec.fees:
                    account_6427 = self.env['account.account'].search([('code', '=', '6427')], limit=1)
                    line_ids.append((0, 0, {
                        'name': "Phí chuyển",
                        'account_id': account_6427.id,
                        'price_unit': rec.fees,
                    }))

                if rec.sender_id.bank_account_id and rec.sender_id.bank_account_id.id:
                    account_1121_bank = rec.sender_id.bank_account_id

                data_unc.update({
                    'name'             : rec.ref,
                    'bank_id'          : rec.sender_id.id,
                    'bank_received_id' : rec.bank_id.id,
                    'acc_number'       : rec.acc_number,
                    'account_id'       : account_1121_bank.id,
                    'partner_id'       : rec.partner_id.id,
                    'line_ids'         : line_ids
                })
                rec.account_voucher_id = obj.create(data_unc)
                rec.account_voucher_id.proforma_voucher()
                if rec.account_voucher_id.sale_id and rec.account_voucher_id.sale_id.id:
                    rec.account_voucher_id.move_id.line_ids.write({
                        'sale_id': rec.account_voucher_id.sale_id.id,
                    })
                rec.write({'state': 'done'})

    @api.multi
    def set_status_unc_to_draft(self):
        return self.write({
            'state': 'draft'
        })

    @api.multi
    def set_status_unc_to_cancel(self):
        for rec in self:
            if rec.account_voucher_id:
                rec.account_voucher_id.cancel_voucher()
                rec.account_voucher_id.unlink()
                return self.write({
                    'state': 'cancel'
                })

