# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError,Warning
from datetime import datetime
from lxml import etree

class account_gbn(models.Model):
    _name = 'account.payment.gbn'
    # _description = 'Giấy báo có'

    state          = fields.Selection([
        ('draft', 'Bản phác thảo'),
        # ('KT_doing', 'Giám đốc duyệt'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Huỷ')
    ], string='Trạng thái', default='draft')

    sender_id      = fields.Many2one('res.partner', string='Người nhận', domain="[('bank','=',True)]")
    partner_id     = fields.Many2one('res.partner', string='Người gửi', domain="[('bank','!=',True)]")
    bank_id        = fields.Many2one('res.partner', string='Ngân hàng', domain="[('bank','=',True), ('parent_id', '=', False)]")
    amount         = fields.Float(string='Số tiền')
    date_unc       = fields.Date(string='Ngày tạo')
    ref            = fields.Char('Tham chiếu')
    note           = fields.Char(string='Diễn giải', default="Thu"
                                                             "")
    gbn_acc_pay_id = fields.Many2one('account.payment', required=False, ondelete='cascade', index=True, copy=False)
    gbn_acc_inv_id = fields.Many2one('account.invoice', required=False, ondelete='cascade', index=True, copy=False)
    acc_number     = fields.Char('Account Number')
    date_create    = fields.Date('Ngày tạo', default=fields.Date.context_today)
    journal_id     = fields.Many2one('account.journal', string='Sổ kế toán')
    account_id     = fields.Many2one('account.account', string='Tài khoản')
    record_checked = fields.Boolean('Done')
    move_id        = fields.Many2one('account.move', string='Bút toán')

    @api.multi
    def unlink(self):
        if any([rec.state == 'done' for rec in self]):
            raise Warning(_('Không thể xoá UNT đã hoàn thành'))
        res = super(account_gbn, self).unlink()
        return res

    @api.constrains('ref')
    def _check_public_holiday(self):
        for rec in self:
            if rec.ref:
                unc_ids = rec.search([('ref', '=', rec.ref)])
                if unc_ids and len(unc_ids) > 1:
                    raise ValidationError(_('Tham Chiếu phải là duy nhất!'))

    @api.multi
    def change_record_checked(self):
        for record in self:
            if not record.record_checked:
                record.record_checked = True
            else:
                record.record_checked = False

    def update_check_account_payment_gbn(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        for order in orderlines:
            order.record_checked = False

    @api.onchange('partner_id','bank_id')
    def onchange_partner_bank(self):
        if self.partner_id and self.bank_id:
            bank_ids = self.env['res.partner.bank'].search([('partner_id','=',self.partner_id.id),('bank_partner_id','=',self.bank_id.id)])
            if bank_ids and len(bank_ids) ==1:
                self.acc_number = bank_ids.acc_number

    @api.onchange('partner_id')
    def filter_bank(self):
        if self.partner_id:
            return {'domain': {'bank_id':[('id','in',self.partner_id.bank_ids.mapped('bank_partner_id').ids)]}}


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(account_gbn, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                       toolbar=toolbar, submenu=submenu)
        if self._context and 'status' in self._context and self._context.get('status') == 'paid':
            if view_type in 'tree':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                first_node = doc.xpath("//tree")[0]
                first_node.set('create', 'false')
                res['arch'] = etree.tostring(doc)
            if view_type in 'form':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                second_node = doc.xpath("//form")[0]
                second_node.set('create', 'false')
                res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def default_get(self, fields):
        res = super(account_gbn, self).default_get(fields)
        if 'active_id' in self._context:
            acc_pay = False

            if 'active_model' in self._context and self._context['active_model'] == 'account.invoice':
                acc_pay = self.env['account.invoice'].browse(self._context['active_id'])
            elif 'active_model' in self._context and self._context['active_model'] == 'account.payment':
                acc_pay = self.env['account.payment'].browse(self._context['active_id'])

            if acc_pay:
                res['partner_id'] = acc_pay.partner_id.id
                res['date_unc'] = datetime.today().date().strftime('%Y-%m-%d')

                if 'active_model' in self._context and self._context['active_model'] == 'account.invoice':
                    res['amount'] = acc_pay.residual
                    res['gbn_acc_inv_id'] = acc_pay.id
                    res['note'] = acc_pay.origin
                elif 'active_model' in self._context and self._context['active_model'] == 'account.payment':
                    res['amount'] = acc_pay.amount
                    res['gbn_acc_pay_id'] = acc_pay.id
                    res['note'] = acc_pay.communication
        else:
            journal = self.env['account.journal'].search([
                ('type', '=', 'bank'),
            ], limit=1)
            if journal and journal.id:
                res['journal_id'] = journal.id

            account = self.env['account.account'].search([
                ('code', '=', '131'),
            ], limit=1)
            if account and account.id:
                res['account_id'] = account.id

        return res

    @api.multi
    def multi_change_status_gbn(self):
        ids = self.env.context.get('active_ids', [])
        gbn_ids = self.browse(ids)
        for gbn in gbn_ids:
            if gbn.state == 'draft':
                gbn.change_status_gbn()

    @api.multi
    def change_status_gbn(self):
        self.ensure_one()

        # if self.state == 'draft':
        #     return self.write({'state': 'KT_doing'})

        if self.state == 'draft':
            if self.gbn_acc_pay_id:
                self.gbn_acc_pay_id.amount = self.amount
                self.gbn_acc_pay_id.action_post_new()
            if self.gbn_acc_inv_id:
                journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
                payment_type = 'inbound'
                payment_methods = journal.outbound_payment_method_ids
                payment_method_id = payment_methods and payment_methods[0] or False
                partner_type = 'customer'
                invoice_ids = [self.gbn_acc_inv_id.id]
                account_payment_infor = {
                    # 'name': 'Draft Payment',
                    'invoice_ids' : [(6,0,invoice_ids)],
                    'payment_type': payment_type,
                    'partner_type': partner_type,
                    'partner_id': self.partner_id.id,
                    'payment_method_id': payment_method_id.id,
                    'journal_id' : journal.id,
                    'amount': self.amount,
                    'payment_date': self.date_create or datetime.now().strftime('%Y-%m-%d'),
                }
                account_payment = self.env['account.payment'].create(account_payment_infor)
                account_payment.post()
            else:
                self.env['account.payment'].create(self.account_unc_payment_create())
                # Tao but toan dua vao cong no nha cung cap
                line_ids = [(0, 0, {
                    'name': self.note or 'Thu tiền theo phiếu thu số %s' % (self.ref or '',),
                    'account_id': self.journal_id and self.journal_id.default_debit_account_id and self.journal_id.default_debit_account_id.id,
                    'debit': self.amount,
                    'partner_id': self.sender_id and self.sender_id.id or False,
                }), (0, 0, {
                    'name': self.note or 'Thu tiền theo phiếu thu số %s' % (self.ref or '',),
                    'account_id': self.account_id and self.account_id.id,
                    'credit': self.amount,
                    'partner_id': self.partner_id and self.partner_id.id or False,
                })]
                move_data = {
                    'journal_id': self.journal_id and self.journal_id.id or False,
                    'date': self.date_create or datetime.now().strftime('%Y-%m-%d'),
                    'ref': self.ref or '',
                    'line_ids': line_ids,
                }

                move = self.env['account.move'].create(move_data)
                move.post()

                self.move_id = move

            return self.write({'state': 'done'})

    @api.multi
    def account_unc_payment_create(self):
        payment_methods = self.journal_id.outbound_payment_method_ids
        payment_type = 'inbound'
        partner_type = 'customer'
        sequence_code = 'account.payment.customer.invoice'
        name = self.env['ir.sequence'].with_context(ir_sequence_date=self.date_unc).next_by_code(sequence_code)
        return {
            'name': name,
            'payment_type': payment_type,
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'partner_type': partner_type,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'amount': self.amount,
            'currency_id': self.env.user.company_id.currency_id.id,
            'payment_date': self.date_create,
            'journal_id': self.journal_id.id,
            'company_id': self.env.user.company_id.id,
            'communication': self.note,
            'state': 'reconciled',
            'original_documents': self.ref,
        }

    @api.multi
    def set_status_gbn_to_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def set_status_gbn_to_cancel(self):
        for rec in self:
            if rec.move_id:
                rec.move_id.button_cancel()
                rec.move_id.unlink()
                return self.write({'state': 'cancel'})
            else:
                raise Warning(_('Không thể huỷ UNT'))
