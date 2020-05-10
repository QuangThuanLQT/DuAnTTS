# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, Warning
from datetime import datetime
import math

class account_unc_modifier(models.Model):
    _inherit = "account.payment.unc"

    company_id = fields.Many2one('res.company',default=1)
    state = fields.Selection(
        [
            ('draft', 'Bản phác thảo'),
            # ('GD_doing', 'Giám đốc duyệt'),
            ('done', 'Hoàn thành'),
            ('cancel', 'Huỷ')
        ],
        string='Trạng thái',
        default='draft'
    )
    acc_number = fields.Char('Account Number')
    note = fields.Char(string='Diễn giải', default="Chi")

    @api.multi
    def unlink(self):
        if any([rec.state == 'done' for rec in self]):
            raise Warning(_('Không thể xoá UNC đã hoàn thành'))
        res = super(account_unc_modifier, self).unlink()
        return res

    @api.constrains('ref')
    def _check_public_holiday(self):
        for rec in self:
            if rec.ref:
                unc_ids = rec.search([('ref', '=', rec.ref)])
                if unc_ids and len(unc_ids) > 1:
                    raise ValidationError(_('Tham Chiếu phải là duy nhất!'))

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

    @api.multi
    def multi_change_status_unc(self):
        ids = self.env.context.get('active_ids', [])
        unc_ids = self.browse(ids)
        for unc in unc_ids:
            if unc.state == 'draft':
                unc.change_status_unc()

    # @api.multi
    # def update_ref_account_move_line(self):
    #     unc_ids = self.env['account.payment.unc'].search([])
    #     for unc_id in unc_ids:
    #         if unc_id.move_id:
    #             for line in unc_id.move_id.line_ids:
    #                 if line.account_id.code == '1121':
    #                     self._cr.execute(
    #                         """UPDATE account_move_line SET name='%s' WHERE id=%s""" % (unc_id.note, line.id))
    #                     self._cr.commit()
    #                 elif line.account_id.code == '632':
    #                     self._cr.execute(
    #                         """UPDATE account_move_line SET partner_id='%s' WHERE id=%s""" % (unc_id.partner_id.id, line.id))
    #                     self._cr.commit()
    #         else:
    #             if unc_id.ref:
    #                 move_id = self.env['account.move'].search([('ref','=',unc_id.ref)])
    #                 if len(move_id) > 1:
    #                     print "----------%s"%(unc_id.ref)
    #                 elif move_id:
    #                     for line in move_id.line_ids:
    #                         if line.account_id.code == '1121':
    #                             self._cr.execute(
    #                                 """UPDATE account_move_line SET name='%s' WHERE id=%s""" % (unc_id.note, line.id))
    #                             self._cr.commit()
    #                         elif line.account_id.code == '6428':
    #                             self._cr.execute(
    #                                 """UPDATE account_move_line SET partner_id='%s' WHERE id=%s""" % (
    #                                 unc_id.partner_id.id, line.id))
    #                             self._cr.commit()


    @api.multi
    def change_status_unc(self):

        # if self.state == 'draft':
        #     return self.write({'state': 'GD_doing'})

        if self.state == 'draft':
            if self.acc_pay_id:
                if self.acc_pay_id.state != 'reconciled':
                    self.acc_pay_id.write({'state': 'reconciled'})
            if self.acc_inv_id:
                journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
                payment_type = 'outbound'
                payment_methods = journal.outbound_payment_method_ids
                payment_method_id = payment_methods and payment_methods[0] or False
                partner_type = 'supplier'
                invoice_ids = [self.acc_inv_id.id]
                account_payment_infor = {
                    # 'name': 'Draft Payment',
                    'invoice_ids': [(6, 0, invoice_ids)],
                    'payment_type': payment_type,
                    'partner_type': partner_type,
                    'partner_id': self.partner_id.id,
                    'payment_method_id': payment_method_id.id,
                    'journal_id': journal.id,
                    'amount': self.amount,
                    'payment_date': self.date_create or datetime.now().strftime('%Y-%m-%d'),
                }
                account_payment = self.env['account.payment'].create(account_payment_infor)
                account_payment.post()
            else:
                self.env['account.payment'].create(self.account_unc_payment_create())
                # Tao but toan dua vao cong no nha cung cap
                line_ids = [(0, 0, {
                    'name': self.note or 'Chi tiền theo phiếu chi số %s' % (self.ref or '',),
                    'partner_id': self.sender_id and self.sender_id.id or False,
                    'account_id': self.journal_id and self.journal_id.default_credit_account_id and self.journal_id.default_credit_account_id.id,
                    'credit': self.amount + self.fees,
                }), (0, 0, {
                    'name': 'Chi tiền theo phiếu chi số %s' % (self.ref or '',),
                    'account_id': self.account_id and self.account_id.id,
                    'debit': self.amount,
                    'partner_id': self.partner_id and self.partner_id.id or False,
                })]
                if self.fees:
                    account_fees = self.env['account.account'].search([
                        ('code', '=', '6428'),
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
    def account_unc_payment_create(self):
        payment_methods = self.journal_id.outbound_payment_method_ids
        payment_type = 'outbound'
        partner_type = 'supplier'
        sequence_code = 'account.payment.supplier.invoice'
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
            'original_documents' : self.ref,
        }

    def DocSo3ChuSo(self, baso):
        ChuSo = [" không", " một", " hai", " ba", " bốn", " năm", " sáu", " bảy", " tám", " chín"]
        KetQua = ""
        tram = int(baso/100)
        chuc = int((baso%100)/10)
        donvi = int(baso%10)

        if (tram==0 and chuc==0 and donvi==0):
            return ""

        if (tram!=0):
            KetQua += ChuSo[tram] + " trăm"
            if ((chuc == 0) and (donvi != 0)):
                KetQua += " linh "
        if ((chuc != 0) and (chuc != 1)):
            KetQua += ChuSo[chuc] + " mươi"
            if ((chuc == 0) and (donvi != 0)):
                KetQua = KetQua + " linh"

        if (chuc == 1):
            KetQua += " mười "

        if donvi == 1:
            if ((chuc != 0) and (chuc != 1)):
                KetQua += " mốt "
            else:
                KetQua += ChuSo[donvi]
        elif donvi == 5:
            if (chuc == 0):
                KetQua += ChuSo[donvi]
            else:
                KetQua += " lăm "
        else:
            if (donvi != 0):
                KetQua += ChuSo[donvi]
        return KetQua

    def DocTienBangChu(self, SoTien):
        Tien = ["", " nghìn", " triệu", " tỷ", " nghìn tỷ", " triệu tỷ"]
        KetQua = ""
        ViTri = {}
        if (SoTien < 0):
            return "Số tiền âm"
        elif (SoTien == 0):
            return "Không"
        if (SoTien > 0):
            so = SoTien
        else:
            so = -SoTien
        if (SoTien > 8999999999999999):
            return "Số quá lớn"

        ViTri[5] = math.floor(so / 1000000000000000)
        if (math.isnan(ViTri[5])):
            ViTri[5] = "0"
        so = so - float(ViTri[5]) * 1000000000000000
        ViTri[4] = math.floor(so / 1000000000000)
        if (math.isnan(ViTri[4])):
            ViTri[4] = "0"
        so = so - float(ViTri[4]) * 1000000000000
        ViTri[3] = math.floor(so / 1000000000)
        if (math.isnan(ViTri[3])):
            ViTri[3] = "0"
        so = so - float(ViTri[3]) * 1000000000
        ViTri[2] = int(so / 1000000)
        if (math.isnan(ViTri[2])):
            ViTri[2] = "0"
        ViTri[1] = int((so % 1000000) / 1000)
        if (math.isnan(ViTri[1])):
            ViTri[1] = "0"
        ViTri[0] = int(so % 1000)
        if (math.isnan(ViTri[0])):
            ViTri[0] = "0"
        if (ViTri[5] > 0):
            lan = 5
        elif (ViTri[4] > 0):
            lan = 4
        elif (ViTri[3] > 0):
            lan = 3
        elif (ViTri[2] > 0):
            lan = 2
        elif (ViTri[1] > 0):
            lan = 1
        else:
            lan = 0
        i = lan
        while i >= 0:
            tmp = self.DocSo3ChuSo(ViTri[i])
            KetQua += tmp
            if (ViTri[i] > 0):
                KetQua += Tien[i]
            if ((i > 0) and (len(tmp) > 0)):
                KetQua += ''
            i -= 1

        if (KetQua[len(KetQua) - 1:] == ','):
            KetQua = KetQua[0: len(KetQua) - 1]
        KetQua = KetQua[1: 2].upper() + KetQua[2:]
        return KetQua