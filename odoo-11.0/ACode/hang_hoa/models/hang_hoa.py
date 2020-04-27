# -*- coding: utf-8 -*-

from odoo import models, fields, api


class khachhang(models.Model):
    _inherit = 'res.partner'

class kho(models.Model):
    _inherit = 'stock.warehouse'

class sanpham(models.Model):
    _inherit = 'product.template'

class hanghoaqt(models.Model):
    _name = 'hang.hoa.qt'

    ten_sp = fields.Char(string='Tên sản phẩm')
    sale_ok = fields.Boolean('Có thể bán', default=True)
    purchase_ok = fields.Boolean('Có thể Mua được', default=True)

    loai_sp = fields.Selection([
        ('1', 'Service'),
        ('2', 'Stockable Product'),
        ('3', 'Consumable')],
        string='Loại sản phẩm', required=True, default='1')
    tham_chieu_nb = fields.Char(string='Tham chiếu nội bộ')
    ma = fields.Char(string='Mã')
    nha_cung_cap = fields.Many2one('res.partner', string='Nhà cung cấp')
    kho_ngam_dinh = fields.Many2one('stock.location', string='Kho ngầm định')
    gia_ban = fields.Integer(string='Giá bán')
    chi_phi = fields.Integer(string='Chi phí')
    ton_kho = fields.Integer(string='Tồn kho')
    dvt = fields.Many2one('product.uom.categ', string='Đơn vị tính')

class phieuxuat(models.Model):
    _inherit = 'stock.picking'

    dia_diem_den = fields.Char(string='Địa điểm đến', required=1)
    dia_diem_nguon = fields.Char(string='Địa điểm nguồn', required=1)
    ly_do = fields.Char(string='Lý do xuất')
    chu_so_huu = fields.Many2one('res.partner', string='Chủ sở hữu')
    don_hang = fields.Char(string='Đơn hàng')

class MyPipeline(models.Model):
    _inherit = 'crm.lead'
