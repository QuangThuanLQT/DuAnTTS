# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import math


class sale_order_return(models.Model):
    _name = 'sale.order.return'

    name = fields.Char(string='Reference return', readonly=True, required=True, copy=False, default='New')
    don_tra_hang = fields.Boolean(default=False)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    # sale_order_return_ids = fields.Char(string="Sale Order")
    sale_order_return_ids = fields.Many2one('sale.order', string="Sale Order",
                                            domain="[('partner_id', '=', partner_id)]", required=True)
    # reason_cancel = fields.Many2one('ly.do.tra.hang', string='Lý do', required=True)
    reason_cancel = fields.Selection(
        [('sp_loi', 'Sản phẩm lỗi'),
         ('kho_soan_thieu', 'Kho soạn thiếu hàng'),
         ('sai_hang', 'Sai hàng'), ('khach_doi_y', 'Khách đổi ý'),
         ('khach_huy_don', 'Khách huỷ đơn')],
        string='Lý do trả hàng', default='sp_loi', required=1, store=True)

    receive_method = fields.Selection(
        [('allow', 'Nhận hàng trả lại tại kho'), ('stop', 'Nhận hàng trả lại tại địa chỉ giao hàng')],
        string="Phương thức nhận hàng", required=True)
    location_return = fields.Selection([('allow', 'Kho Bình thường'), ('stop', 'Kho hư hỏng')],
                                       string="Kho lưu trữ sản phẩm", required=True)
    note = fields.Text(string='Diễn giải')
    # ...................
    confirmation_date = fields.Datetime(string='Confirmation Date', compute=False, store=True, index=True,
                                        readonly=True, help="Date on which the sales order is confirmed.",
                                        default=fields.Datetime.now)
    so_tien_da_tra = fields.Float(string='Số tiền đã trả')
    con_phai_tra = fields.Float(string='Số tiền còn phải trả', compute='_con_phai_tra')
    trang_thai_tt = fields.Selection(
        [('chua_tt', 'Chưa thanh toán'),
         ('tt_1_phan', 'Thanh toán 1 phần'),
         ('done_tt', 'Hoàn tất thanh toán')],
        string='Trạng thái thanh toán', default='chua_tt', required=1)
    trang_thai_dh = fields.Selection([
        ('waiting_pick', 'Chờ đợi để chọn'), ('ready_pick', 'Sẵn sàng để nhặt'), ('picking', 'Chọn'),
        ('waiting_pack', 'Chờ đợi để đóng gói'), ('packing', 'Đóng gói'),
        ('waiting_delivery', 'Chờ giao hàng'), ('delivery', 'Cung cấp'),
        ('reveive', 'Nhận được'), ('waiting', 'Chờ đợi để kiểm tra'), ('checking', 'Kiểm tra'),
        ('done', 'Hoàn thành'),
        ('reverse_tranfer', 'Đảo ngược'),
        ('cancel', 'Đã huỷ')
    ], string='Trạng thái đơn hàng', store=True)
    create_uid = fields.Many2one('res.users', 'Created by', index=True, readonly=True)
    confirm_user_id = fields.Many2one('res.users', string='Validate by', readonly=True)
    state_return = fields.Selection([
        ('draft', 'Draft'),
        ('order_return', 'Order Return')], default='draft', string='Status')
    # ----------------------chuyển sô tiền qua string

    total_text = fields.Char('Total Text', compute='_compute_total')

    def DocSo3ChuSo(self, baso):
        ChuSo = [" không", " một", " hai", " ba", " bốn", " năm", " sáu", " bảy", " tám", " chín"]
        KetQua = ""
        tram = int(baso / 100)
        chuc = int((baso % 100) / 10)
        donvi = baso % 10

        if (tram == 0 and chuc == 0 and donvi == 0):
            return ""

        if (tram != 0):
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

    # ...thay đổi tiền lý do tra...
    @api.onchange('reason_cancel')
    def onchange_reason_cancel(self):
        if self.reason_cancel == 'sp_loi':
            self.So_tien_tra_lai = 'tralai100'
        if self.reason_cancel == 'kho_soan_thieu':
            self.So_tien_tra_lai = 'tralai100'
        if self.reason_cancel == 'sai_hang':
            self.So_tien_tra_lai = 'tralai100'
        if self.reason_cancel == 'khach_doi_y':
            self.So_tien_tra_lai = 'tralai50'
        if self.reason_cancel == 'khach_huy_don':
            self.So_tien_tra_lai = 'tralai50'

    @api.multi
    def _compute_total(self):
        for record in self:
            subtotal = record.amount_total
            total_text = self.env['sale.order.return'].DocTienBangChu(subtotal)
            record.total_text = total_text

    @api.onchange('sale_order_return_ids')
    def onchange_sale_order_return_ids(self):
        if self.sale_order_return_ids:
            for line in self.sale_order_return_ids.order_line:
                self.order_line_ids += self.order_line_ids.new({
                    'product_id': line.product_id.id,
                    'invoice_name': line.product_id.name,
                    'price_unit': line.price_unit,
                    'amount_tax': line.tax_id,
                    # 'discount': line.discount,
                    'product_uom': line.product_uom,
                    # 'price_discount': line.price_discount,
                    'product_uom_qty': 0,
                })

    @api.multi
    def order_return(self):
        self.state_return = 'order_return'

    # ...................
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.order.return') or 'New'
        result = super(sale_order_return, self).create(vals)
        return result

    # ...................
    @api.multi
    def _con_phai_tra(self):
        for rec in self:
            rec.con_phai_tra = rec.amount_total - rec.so_tien_da_tra

    order_line_ids = fields.One2many('order.line', 'order_line_id')

    # tax_id = fields.Char(string='Thuế')
    tax_id = fields.Many2one('account.tax', string='Thuế')
    discount_type = fields.Selection([('percent', 'Tỷ lên phần trăm'), ('amount', 'Số tiền')],
                                     string='Loại giảm giá', default='percent')
    discount_rate = fields.Float('Tỷ lệ chiết khấu')
    check_box_co_cq = fields.Boolean(default=False, string="CO, CQ")
    check_box_invoice_gtgt = fields.Boolean(default=False, string="Invoice GTGT")

    total_quantity = fields.Float(string='Tổng số lượng', compute='_get_total_quantity', readonly=True, digits=(16, 0))
    amount_untaxed = fields.Float(string='Untaxed Amount', compute='_untax_amount', readonly=True, digits=(16, 0))
    amount_tax = fields.Float(string='Taxes', readonly=True, digits=(16, 0))
    amount_total = fields.Float(string='Total', compute='_amount_all', readonly=True, digits=(16, 0))

    So_tien_tra_lai = fields.Selection([('tralai100', '100%'), ('tralai50', '50%')],
                                       string='Số tiền hoàn lại')

    @api.depends('order_line_ids.product_uom_qty')
    def _get_total_quantity(self):
        for rec in self:
            total_quantity = 0
            for line in rec.order_line_ids:
                total_quantity += line.product_uom_qty
            rec.total_quantity = total_quantity

    @api.depends('order_line_ids.price_subtotal', 'amount_untaxed')
    def _untax_amount(self):
        for rec in self:
            amount_untaxed = 0
            for line in rec.order_line_ids:
                amount_untaxed += line.price_subtotal
            rec.amount_untaxed = amount_untaxed

    # ................tính lại tiền theo lý do trả.....................
    @api.depends('order_line_ids.price_subtotal', 'So_tien_tra_lai')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line_ids:
                amount_untaxed += line.price_subtotal

            if order.So_tien_tra_lai == 'tralai50':
                order.update({
                    'amount_total': (amount_untaxed + amount_tax) / 2
                })
            else:
                order.update({
                    'amount_total': amount_untaxed + amount_tax
                })

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, "%s - %s" % (record.name, record.partner_id.name)))
        return res


class thong_tin_order_line(models.Model):
    _name = 'order.line'

    order_line_id = fields.Many2one('sale.order.return')
    product_id = fields.Many2one('product.product', string='Sản phẩm')
    invoice_name = fields.Char(string='Tên Hoá Đơn')
    product_uom_qty = fields.Float(string='SL trả lại', default=1.0)
    # check_box_prinizi_confirm = fields.Boolean(default=False, string="Xác nhận in")
    # print_qty = fields.Float(string='In sô lượng', digits=(16, 0))
    # sl_dat_hang = fields.Float(string="SL đặt hàng")
    price_unit = fields.Float(string='Đơn giá', default=0.0)
    price_subtotal = fields.Float(string='Tổng phụ', compute='_compute_amount', default=0.0)

    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty(self):
        if self.product_uom_qty and self.order_line_id.sale_order_return_ids:
            line_ids = self.order_line_id.sale_order_return_ids.order_line.filtered(
                lambda line: line.product_id == self.product_id)
            if self.product_uom_qty > sum(line_ids.mapped('product_uom_qty')):
                raise ValidationError(_("Tổng số lượng sp %s trả lại không thể lớn hơn %s." % (
                    line_ids.product_id.name, sum(line_ids.mapped('product_uom_qty')))))

    @api.depends('price_unit', 'product_uom_qty', 'price_subtotal')
    def _compute_amount(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.product_uom_qty

    # lý do trả hàng: lý do là sản phẩm lỗi: hoàn trả lại 100% số tiền
    # lý do là khách đổi ý, khách hủy đơn, hoàn trả lại cho khách hàng 50% số tiền
