# -*- coding: utf-8 -*-

from odoo import models, fields, api


class tts_sms_inbox(models.Model):
    _name = 'tts.sms.inbox'

    date = fields.Datetime('Date', track_visibility='onchange')
    don_hang = fields.Char('Đơn hàng')
    phone = fields.Char('Ngân hàng')
    body = fields.Text(string='Nội dung tin nhắn', store=True, track_visibility='onchange')
    create_uid_voucher = fields.Many2one('res.users', string='Người tạo phiếu thu', track_visibility='onchange')
    create_date_voucher = fields.Datetime(string='Thời gian tạo phiếu thu', track_visibility='onchange')

    amount = fields.Float('Số tiền', track_visibility='onchange')
    ma_kh = fields.Char('Mã KH')
    infor_customer = fields.Selection([
        ('yes', 'Có mã KH'),
        ('no', 'Không có mã KH')], 'TT mã KH', readonly=False, compute=False, store=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng', track_visibility='onchange')
    customer_phone = fields.Char('Điện thoại')
    user_id = fields.Many2one('res.users', string='Nhân viên bán hàng')
    account_voucher_id = fields.Many2one('account.voucher', string='Chi tiết', track_visibility='onchange')

    state = fields.Selection([
        ('draft', 'Chưa tạo phiếu'),
        ('done', 'Đã tạo phiếu')], 'Status', default='draft', readonly=True)

    @api.multi
    def done(self):
        self.state = 'done'

    created_voucher = fields.Boolean()
    add_check = fields.Boolean(compute='get_check_add', store=True)

    @api.depends('body')
    def get_check_add(self):
        for record in self:
            if '+' in record.body:
                record.add_check = True

    def create_account_voucher(self):
        view_id = self.env.ref('account_voucher.view_sale_receipt_form')
        payment_medthod_id = self.env['account.journal'].search([('type', '=', 'bank'), ('bank_name', '=', self.phone)],
                                                                limit=1)
        action = {
            'name': 'Sales Receipts',
            'type': 'ir.actions.act_window',
            'res_model': 'account.voucher',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'target': 'new',
            'context': {
                'default_voucher_type': 'sale',
                'voucher_type': 'sale',
                'default_payment_journal_id': payment_medthod_id.id,
                'payment_journal_id': payment_medthod_id.id,
                'default_partner_id': self.customer_id.id,
                'partner_id': self.customer_id.id,
                'default_amount_input': self.amount,
                'amount_input': self.amount,
                'default_sms_payment_id': self.id,
            }
        }
        return action

    def view_account_voucher(self):
        view_id = self.env.ref('account_voucher.view_sale_receipt_form')
        action = {
            'name': 'Sales Receipts',
            'type': 'ir.actions.act_window',
            'res_model': 'account.voucher',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.account_voucher_id.id,
            'view_id': view_id.id,
            'target': 'current',
        }
        return action

