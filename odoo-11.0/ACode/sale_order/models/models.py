# -*- coding: utf-8 -*-

from odoo import models, fields, api


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


    product_id = fields.Many2one('product.print', string='Product Print')
    vi_tri_in = fields.Many2one('vi.tri.in', tring='Vị trí in', required=1)
    kich_thuot_in = fields.Char('Kích thước in', required=1)
    dien_tich_in = fields.Many2one('prinizi.product.attribute.value', string='Diện tích in')
    noi_dung_in = fields.Char('Nội dung in', required=1)

    sale_id = fields.Many2one('sale.order')


class thong_tin_in_hinh(models.Model):
    _name = 'thong.tin.in.hinh'

    product_id = fields.Many2one('product.print', string='Product Print')
    vi_tri_in = fields.Many2one('vi.tri.in', tring='Vị trí in hình', required=1)
    chat_lieu_in_hinh = fields.Many2one('prinizi.product.attribute.value', string='Chất liệu in hình')
    kich_thuot_in = fields.Char('Kích thước in hình', required=1)
    dien_tich_in = fields.Many2one('prinizi.product.attribute.value', string='Diện tích in', required=1)
    ten_hinh = fields.Char('Tên hình', required=1)

    sale_id = fields.Many2one('sale.order')


class config_thong_tin_its(models.Model):
    _name = 'config.thong.tin.its'


    product_tmpl_id = fields.Many2one('product.template', string='Product Print')
    font_chu_so = fields.Many2one('prinizi.product.attribute.value',string='Font chữ/số mặc định')
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

    @api.depends('phi_its', 'phi_them_its', 'phi_in_hinh')
    def _get_tong_phi_in(self):
        for rec in self:
            rec.tong_phi_in = rec.phi_its + rec.phi_them_its + rec.phi_in_hinh
