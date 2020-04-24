# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api


class tuyenxe(models.Model):
    _name = 'tuyen.xe'


    transporter_id = fields.Many2one('nha.xe.moi', ondelete='cascade', string='Ref ID', required=1)
    name = fields.Char(string='Mã tuyến xe', required=True)
    transporter_name = fields.Char(string='Tên nhà xe', related='transporter_id.name', store=True, readonly=True)
    feosco_city_id = fields.Char(string='Đến Tỉnh/TP')
    feosco_district_id = fields.Char(string='Đến Quận/Huyện')
    phuong_xa = fields.Char(string='Đến Phường/Xã')
    address = fields.Char(string='Đến Địa chỉ')
    thoi_gian_xe_toi = fields.Float(string='Thời gian xe tới', digits=(6, 2), help="Duration in days")
    uoc_tinh_phi_ship = fields.Text(string='Ước tính phí ship')
    note = fields.Text(string='Ghi chú')
    transporter_phone = fields.Char(string='SDT', related='transporter_id.phone_number', store=True, readonly=True)
    transporter_address = fields.Char(string='Address', compute='get_transport_address')

    # @api.depends('transporter_id')
    # def get_transport_address(self):
    #     for record in self:
    #         if record.transporter_id:
    #             address = '%s, %s, %s, %s' % (record.transporter_id.zip,
    #                                           record.transporter_id.street2,
    #                                           record.transporter_id.city,
    #                                           record.transporter_id.street)
    #             record.transporter_address = address

    @api.depends('transporter_id')
    def get_transport_address(self):
        for record in self:
            if record.transporter_id:
                address = '%s, %s, %s, %s' % (record.transporter_id.address,
                                              record.transporter_id.phuong_xa,
                                              record.transporter_id.feosco_district_id,
                                              record.transporter_id.feosco_city_id)
                record.transporter_address = address





