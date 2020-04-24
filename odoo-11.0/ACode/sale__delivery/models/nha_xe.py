# -*- coding: utf-8 -*-

from odoo import models, fields, api


class nhaxemoi(models.Model):
    _name = 'nha.xe.moi'

    name = fields.Char(string='Nhà xe', required=1)
    transporter_code = fields.Char(string='Mã nhà xe', required=1)
    feosco_city_id = fields.Char(string='Đi từ Tỉnh/TP', required=1)
    feosco_district_id = fields.Char(string='Đi từ Quận/Huyện')
    phuong_xa = fields.Char(string='Đi từ Phường/Xã')
    address = fields.Char(string='Đi từ Địa chỉ', required=1)
    phone_number = fields.Char(string='Số điện thoại', required=1)
    time_receive = fields.Char(string='Thời gian nhận hàng')
    ship_type = fields.Selection([('tra_sau', 'Trả sau'), ('tra_truoc', 'Trả trước'), ('ca_hai', 'Cả hai')], required=1,
                                 string="Hình thức thanh toán phí ship")
    note = fields.Text(string='Ghi chú')

    @api.multi
    def write(self, vals):
        res = super(nhaxemoi, self).write(vals)
        return res
