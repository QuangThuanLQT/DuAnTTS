# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class tts_modifier_vendor(models.Model):
    _inherit = 'res.partner'

    ten_nha_cung_cap = fields.Char(string="Tên Nhà cung cấp", required=True)
    trang_thai = fields.Selection([('active', 'Đang hoạt động'), ('unactive', 'Ngưng hoạt động')], string="Trạng thái", required=True)
    nhom_san_pham_cung_cap = fields.Many2many('product.category', string="Nhóm sản phẩm cung cấp", required=True)
    phuong_thuc_giao_hang = fields.Selection(
        [('warehouse', 'Giao hàng tại kho'),
         ('delivery', 'Giao hàng tận nơi'),
         ('transport', 'Giao hàng nhà xe')], string="Phương thức giao hàng", required=True)
    dia_chi_giao_nhan = fields.Char(string="Địa chỉ giao/nhận hàng", required=True)
    web_site = fields.Char(string="Website")

    vendor_payment_method = fields.Selection(
        [('bank', 'Bank'),
         ('cash', 'Cash')], string="Phương thức thanh toán", required=True)
    account_numbers = fields.Char(string="Số tài khoản")
    account_name = fields.Char(string="Tên tài khoản")
    account_bank = fields.Many2one('res.partner', string="Ngân hàng", domain="[('bank', '=', True)]")
    payment_date = fields.Char(string="Thời gian thanh toán")
    liabilities_time = fields.Many2one('liabilities.time', string="Thời gian công nợ")
    liabilities_limit = fields.Float(string="Hạn mức công nợ")


    name_clue_order = fields.Char(string="Họ và Tên")
    phone_clue_order = fields.Char(string="SĐT")
    email_clue_order = fields.Char(string="Email")
    position_title_order = fields.Char(string="Vị trí/Chức danh")
    name_clue_payment = fields.Char(string="Họ và Tên")
    phone_clue_payment = fields.Char(string="SĐT")
    email_clue_payment = fields.Char(string="Email")
    position_title_payment = fields.Char(string="Vị trí/Chức danh")
