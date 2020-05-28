# -*- coding: utf-8 -*-

from odoo import models, fields, api
import math


class thong_tin_its(models.Model):
    _name = 'thong.tin.its'

    product_from_id = fields.Many2one('product.product', string='Product Print')
    lung_tren = fields.Char(string='Lưng trên')
    lung_giua = fields.Char(string='Lưng giữa')
    lung_duoi = fields.Char(string='Lưng dưới')
    in_hinh = fields.Boolean(string='In hình')

    sale_id = fields.Many2one('sale.order')


class thong_tin_them_its(models.Model):
    _name = 'thong.tin.them.its'

    product_id = fields.Many2one('product.product', string='Product Print')
    vi_tri_in = fields.Many2one('vi.tri.in', tring='Vị trí in', required=1)
    kich_thuot_in = fields.Char('Kích thước in', required=1)
    dien_tich_in = fields.Many2one('prinizi.product.attribute.value', string='Diện tích in')
    noi_dung_in = fields.Char('Nội dung in', required=1)

    sale_id = fields.Many2one('sale.order')


class thong_tin_in_hinh(models.Model):
    _name = 'thong.tin.in.hinh'

    product_id = fields.Many2one('product.product', string='Product Print')
    vi_tri_in = fields.Many2one('vi.tri.in', tring='Vị trí in hình', required=1)
    chat_lieu_in_hinh = fields.Many2one('prinizi.product.attribute.value', string='Chất liệu in hình')
    kich_thuot_in = fields.Char('Kích thước in hình', required=1)
    dien_tich_in = fields.Many2one('prinizi.product.attribute.value', string='Diện tích in', required=1)
    ten_hinh = fields.Char('Tên hình', required=1)

    sale_id = fields.Many2one('sale.order')


class config_thong_tin_its(models.Model):
    _name = 'config.thong.tin.its'

    product_tmpl_id = fields.Many2one('product.template', string='Product Print')
    font_chu_so = fields.Many2one('prinizi.product.attribute.value', string='Font chữ/số mặc định')
    lung_ao = fields.Char(string='Lưng áo')
    mat_truoc_ao = fields.Char(string='Mặt trước áo')
    tay_ao = fields.Char(string='Tay áo')
    ong_quan = fields.Char(string='Ống quần')

    sale_id = fields.Many2one('sale.order')


class nhat_ky_lich_su(models.Model):
    _name = 'state.log'

    sale_id = fields.Many2one('sale.order')
    sequence = fields.Integer('Sequence')
    date = fields.Datetime(string='Ngày')
    state = fields.Selection([
        ('waiting_pick', 'Chờ thu cọc'),
        ('ready_pick', 'Chờ lấy hàng'),
        ('picking', 'Đang lấy hàng'),
        ('waiting_pack', 'Chờ đóng gói'),
        ('packing', 'Đang đóng gói'),
        ('waiting_delivery', 'Chờ giao hàng'),
        ('delivery', 'Đang giao hàng'),
        ('reveive', 'Chờ nhận hàng'),
        ('waiting', 'Chờ kiểm hàng'),
        ('checking', 'Đang kiểm hàng'),
        ('done', 'Hoàn tất'),
        ('reverse_tranfer', 'Reverse Tranfer'),
        ('cancel', 'Huỷ'),
        ('block', 'Khóa đơn hàng')
    ], string='Tình trạng hoạt động')


class ProductImage(models.Model):
    _inherit = 'sale.order'

    image_print = fields.Many2many('ir.attachment', string="Image")
    note_image = fields.Text()
    yeu_cau_nhap_hang = fields.One2many('purchase.order', string='Yêu cầu nhập hàng')

    check_all_tt_its = fields.Boolean(string='Checkbox tất cả')
    phi_its = fields.Float(string='Phí in tên số', store=True)
    phi_them_its = fields.Float(string='Phí in thêm tên số', store=True)
    phi_in_hinh = fields.Float(string='Phí in hình', store=True)
    tong_phi_in = fields.Float(string='Tổng phí in', compute='_get_tong_phi_in', store=True, readonly="1")

    thong_tin_its = fields.One2many('thong.tin.its', 'sale_id')
    thong_tin_them_its_ids = fields.One2many('thong.tin.them.its', 'sale_id')
    thong_tin_in_hinh_ids = fields.One2many('thong.tin.in.hinh', 'sale_id')
    config_thong_tin_its_ids = fields.One2many('config.thong.tin.its', 'sale_id')

    state_log_ids = fields.One2many('state.log', 'sale_id')
    total_text = fields.Char('Total Text', compute='_compute_total')

    @api.depends('phi_its', 'phi_them_its', 'phi_in_hinh')
    def _get_tong_phi_in(self):
        for rec in self:
            rec.tong_phi_in = rec.phi_its + rec.phi_them_its + rec.phi_in_hinh



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

    @api.multi
    def _compute_total(self):
        for record in self:
            subtotal = record.amount_total
            total_text = self.env['sale.order'].DocTienBangChu(subtotal)
            record.total_text = total_text


    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, "%s - %s" % (record.name, record.partner_id.name)))
        return res



