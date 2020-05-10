# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from lxml import etree
from odoo.exceptions import Warning


class account_unc(models.Model):
    _name = 'account.payment.unc'

    state          = fields.Selection([
        ('draft', 'Bản phác thảo'),
        ('KT_doing', 'Kế toán trưởng duyệt'),
        ('PGD_doing', 'Phó Tổng Giám Đốc tài chính duyệt'),
        ('TGD_doing', 'Tổng Giám đốc duyệt'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Huỷ')
    ], string='Trạng thái', default='draft')

    ref            = fields.Char('Tham chiếu')
    partner_id     = fields.Many2one('res.partner', string='Người nhận', domain="[('bank','!=',True)]")
    sender_id      = fields.Many2one('res.partner', string='Người gửi', domain="[('bank','=',True)]")
    bank_id        = fields.Many2one('res.partner', string='Ngân hàng',
                              domain="[('bank','=',True), ('parent_id', '=', False)]")
    amount         = fields.Float(string='Số tiền')
    fees           = fields.Float(string='Phí')
    date_unc       = fields.Date(string='Ngày tạo')
    note           = fields.Char(string='Diễn giải')
    acc_pay_id     = fields.Many2one('account.payment', required=False, ondelete='cascade', index=True, copy=False)
    acc_inv_id     = fields.Many2one('account.invoice', required=False, ondelete='cascade', index=True, copy=False)
    date_create    = fields.Date('Ngày tạo', default=fields.Date.context_today)
    journal_id     = fields.Many2one('account.journal', string='Sổ kế toán')
    account_id     = fields.Many2one('account.account', string='Tài khoản')
    record_checked = fields.Boolean('Done')
    move_id        = fields.Many2one('account.move', string='Bút toán')


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
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(account_unc, self).fields_view_get(view_id=view_id, view_type=view_type,
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
        res = super(account_unc, self).default_get(fields)
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
                    res['acc_inv_id'] = acc_pay.id
                    res['note'] = acc_pay.origin
                elif 'active_model' in self._context and self._context['active_model'] == 'account.payment':
                    res['amount'] = acc_pay.amount
                    res['acc_pay_id'] = acc_pay.id
                    res['note'] = acc_pay.communication
        else:
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

    @api.multi
    def change_status_unc(self):
        self.ensure_one()

        if self.state == 'draft':
            return self.write({
                'state': 'KT_doing'
            })

        if self.state == 'KT_doing':
            return self.write({
                'state': 'PGD_doing'
            })

        if self.state == 'PGD_doing':
            return self.write({
                'state': 'TGD_doing'
            })

        if self.state == 'TGD_doing':
            if self.acc_pay_id:
                if self.acc_pay_id.state != 'reconciled':
                    self.acc_pay_id.write({
                        'state': 'reconciled'
                    })
            if self.acc_inv_id:
                journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
                payment_type = 'outbound'
                payment_methods = journal.outbound_payment_method_ids
                payment_method_id = payment_methods and payment_methods[0] or False
                partner_type = 'supplier'
                invoice_ids = [self.acc_inv_id.id]
                account_payment_infor = {
                    # 'name': 'Draft Payment',
                    'invoice_ids' : [(6,0,invoice_ids)],
                    'payment_type': payment_type,
                    'partner_type': partner_type,
                    'partner_id': self.partner_id.id,
                    'payment_method_id': payment_method_id.id,
                    'journal_id' : journal.id,
                    'amount': self.amount,
                    'payment_date': datetime.now().strftime('%Y-%m-%d'),
                }
                account_payment = self.env['account.payment'].create(account_payment_infor)
                account_payment.post()
            else:

                # Tao but toan dua vao cong no nha cung cap
                line_ids = [(0, 0, {
                    'name': 'Chi tiền theo phiếu chi số %s' % (self.ref or '',),
                    'account_id': self.account_id and self.account_id.id,
                    'debit': self.amount,
                    'partner_id': self.partner_id and self.partner_id.id or False,
                }), (0, 0, {
                    'name': 'Chi tiền theo phiếu chi số %s' % (self.ref or '',),
                    'account_id': self.journal_id and self.journal_id.default_credit_account_id and self.journal_id.default_credit_account_id.id,
                    'credit': self.amount + self.fees,
                    'partner_id': self.sender_id and self.sender_id.id or False,
                })]
                if self.fees:
                    account_fees = self.env['account.account'].search([
                        ('code', '=', '6418'),
                    ], limit=1)
                    line_ids.append((0, 0, {
                    'name': 'Phí chi tiền theo phiếu chi số %s' % (self.ref or '',),
                    'account_id': account_fees and account_fees.id,
                    'debit': self.fees,
                    'partner_id': self.partner_id and self.partner_id.id or False,
                }))
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
    def set_status_unc_to_draft(self):
        return self.write({
            'state': 'draft'
        })

    @api.multi
    def set_status_unc_to_cancel(self):
        for rec in self:
            if rec.move_id:
                rec.move_id.button_cancel()
                rec.move_id.unlink()
                return self.write({
                    'state': 'cancel'
                })
            else:
                raise Warning(_('Không thể huỷ UNC'))