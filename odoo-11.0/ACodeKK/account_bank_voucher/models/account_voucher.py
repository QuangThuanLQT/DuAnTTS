# -*- coding: utf-8 -*-

from odoo import models, fields, api
import math

class account_vourcher_inherit(models.Model):
    _inherit = 'account.voucher'

    payment_journal_id         = fields.Many2one(store=True)
    bank_id                    = fields.Many2one('res.partner', string='Ngân hàng', domain="[('bank','=',True), ('bank_type', '=', 'internal')]")
    check_account_journal_bank = fields.Boolean(compute="get_account_journal_bank")
    acc_number                 = fields.Char('Số tài khoản')
    bank_received_id           = fields.Many2one('res.partner', string='Ngân hàng nhận',domain="[('bank','=',True), ('bank_type', '=', 'internal')]")

    @api.onchange('partner_id', 'bank_received_id')
    def onchange_partner_bank(self):
        if self.partner_id and self.bank_received_id:
            bank_ids = self.env['res.partner.bank'].search(
                [('partner_id', '=', self.partner_id.id), ('bank_partner_id', '=', self.bank_received_id.id)])
            if bank_ids and len(bank_ids) == 1:
                self.acc_number = bank_ids.acc_number
            elif not bank_ids:
                self.acc_number = False

    @api.onchange('payment_journal_id')
    def get_account_journal_bank(self):
        journal_bank_id = self.env['account.journal'].search([('code', '=', 'BNK1')], limit=1).id
        if journal_bank_id == self.payment_journal_id.id:
            self.check_account_journal_bank = True
        else:
            self.check_account_journal_bank = False

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        move_line = super(account_vourcher_inherit, self).first_move_line_get(move_id, company_currency, current_currency)
        if move_line:
            move_line.update({
                'partner_id': self.bank_id.id or self.partner_id.id,
            })
            if self.bank_id.bank_account_id.id:
                move_line.update({'account_id': self.bank_id.bank_account_id.id})
        return move_line

    @api.model
    def default_get(self, fields):
        res = super(account_vourcher_inherit, self).default_get(fields)
        if self._context and 'unt_unc' in self._context:
            res['payment_journal_id'] = self.env['account.journal'].search([('code', '=', 'BNK1')], limit=1).id
        else:
            res['payment_journal_id'] = self.env['account.journal'].search([('code', '=', 'CSH1')], limit=1).id
        return res

    @api.depends('company_id', 'pay_now', 'account_id')
    def _compute_payment_journal_id(self):
        for voucher in self:
            if voucher.pay_now != 'pay_now':
                continue
            if self._context and 'unt_unc' in self._context:
                domain = [
                    ('type', '=', 'bank'),
                    ('company_id', '=', voucher.company_id.id),
                ]
            else:
                domain = [
                    ('type', '=', 'cash'),
                    ('company_id', '=', voucher.company_id.id),
                ]
            voucher.payment_journal_id = self.env['account.journal'].search(domain, limit=1)
            voucher.account_id = voucher.payment_journal_id.default_debit_account_id

    def DocSo3ChuSo(self, baso):
        ChuSo = [" không", " một", " hai", " ba", " bốn", " năm", " sáu", " bảy", " tám", " chín"]
        KetQua = ""
        tram = int(baso/100)
        chuc = int((baso%100)/10)
        donvi = baso%10

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

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_account_112(self):
        bank_account_id = self.env['account.account'].search([('code','=','1121')])
        if bank_account_id:
            return bank_account_id[0].id

    bank_account_id     = fields.Many2one('account.account',string='Tài Khoản Ngân Hàng',default=get_account_112)

