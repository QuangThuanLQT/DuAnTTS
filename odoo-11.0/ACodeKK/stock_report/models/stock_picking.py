# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math
from odoo import fields, models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    total = fields.Float('Sale Total')
    total_text = fields.Char('Total Text', compute='_compute_total')
    sale_id = fields.Many2one('sale.order', string="Sale Total", compute='_compute_sale_order')

    @api.multi
    def do_print_picking(self):
        self.write({'printed': True})
        return self.env["report"].get_action(self, 'stock_report.report_delivery_note')

    @api.multi
    def get_co_cq(self):
        for record in self:
            if record.group_id and 'SO' in record.group_id.name:
                sale_order_id = self.env['sale.order'].search([('name','=',record.group_id.name)])
                if sale_order_id and sale_order_id.check_box_co_cq:
                    return True
                else:
                    return False
            if record.group_id and 'PO' in record.group_id.name:
                purchase_order_id = self.env['purchase.order'].search([('name', '=', record.group_id.name)])
                if purchase_order_id and purchase_order_id.check_box_co_cq:
                    return True
                else:
                    return False
            return False

    @api.multi
    def get_invoice_gtgt(self):
        for record in self:
            if record.group_id and 'SO' in record.group_id.name:
                sale_order_id = self.env['sale.order'].search([('name', '=', record.group_id.name)])
                if sale_order_id and sale_order_id.check_box_invoice_gtgt:
                    return True
                else:
                    return False
            if record.group_id and 'PO' in record.group_id.name:
                purchase_order_id = self.env['purchase.order'].search([('name', '=', record.group_id.name)])
                if purchase_order_id and purchase_order_id.check_box_invoice_gtgt:
                    return True
                else:
                    return False
            return False

    @api.multi
    def _compute_sale_order(self):
        for record in self:
            for move in record.move_lines:
                if move.group_id and move.group_id.id:
                    sale_id = self.env['sale.order'].search([
                        ('procurement_group_id', '=', move.group_id.id),
                    ], limit=1)
                    record.sale_id = sale_id

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
            tmp = self.DocSo3ChuSo(int(ViTri[i]))
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

    @api.multi
    def _compute_total(self):
        for record in self:
            sale_id = None
            for move in record.move_lines:
                if move.group_id and move.group_id.id:
                    sale_id = self.env['sale.order'].search([
                        ('procurement_group_id', '=', move.group_id.id),
                    ], limit=1)
                    break

            subtotal = sale_id and sale_id.amount_total or 0
            total_text = self.DocTienBangChu(subtotal)
            record.total_text = total_text

    @api.model
    def total_text(self,amount):
        total_text = self.DocTienBangChu(amount)
        return total_text

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(StockPicking, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
    #     if view_type == 'form' and res.get('toolbar', False) and 'print' in res['toolbar']:
    #         del res['toolbar']['print']
    #     return res