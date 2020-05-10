# -*- coding: utf-8 -*-

from odoo import models, fields, api


class tts_transporter(models.Model):
    _name = 'tts.transporter'

    name = fields.Char(string='Nhà xe', required=1)
    transporter_code = fields.Char(string='Mã nhà xe', required=1)
    feosco_city_id = fields.Many2one('feosco.city', u'Đi từ Tỉnh/TP', required=1)
    feosco_district_id = fields.Many2one('feosco.district', u'Đi từ Quận/Huyện',
                                         domain="[('city_id', '=', feosco_city_id)]", required=1)
    phuong_xa = fields.Many2one('feosco.ward', string='Đi từ Phường/Xã',
                                domain="[('district_id', '=', feosco_district_id)]",
                                required=1)
    address = fields.Char(string='Đi từ Địa chỉ', required=1)
    phone_number = fields.Char(string='Số điện thoại', required=1)
    time_receive = fields.Char(string='Thời gian nhận hàng')
    ship_type = fields.Selection([('tra_sau', 'Trả sau'), ('tra_truoc', 'Trả trước'), ('ca_hai', 'Cả hai')], required=1,
                                 string="Hình thức thanh toán phí ship")
    note = fields.Text(string='Ghi chú')

    @api.model
    def create(self, vals):
        res = super(tts_transporter, self).create(vals)
        feosco_district_id = self.env['feosco.district'].search(
            [('city_id', '=', res.feosco_city_id.id), ('name', '=', res.feosco_district_id.name)], limit=1)
        if feosco_district_id:
            res.feosco_district_id = feosco_district_id
            phuong_xa = self.env['feosco.ward'].search(
                [('district_id', '=', res.feosco_district_id.id), ('name', '=', res.phuong_xa.name)], limit=1)
            if phuong_xa:
                res.phuong_xa = phuong_xa
        return res

    @api.multi
    def write(self, vals):
        res = super(tts_transporter, self).write(vals)
        return res
