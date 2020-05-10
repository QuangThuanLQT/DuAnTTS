# -*- coding: utf-8 -*-

from odoo import models, fields, api


class tts_transporter_route(models.Model):
    _name = 'tts.transporter.route'

    transporter_id = fields.Many2one('tts.transporter', string='Ref ID', required=1)
    name = fields.Char(string='Mã tuyến xe', required=True)
    transporter_name = fields.Char(string='Tên nhà xe', related='transporter_id.name', store=True, readonly=True)
    feosco_city_id = fields.Many2one('feosco.city', u'Đến Tỉnh/TP', required=1)
    feosco_district_id = fields.Many2one('feosco.district', u'Đến Quận/Huyện',
                                         domain="[('city_id', '=', feosco_city_id)]", required=1)
    phuong_xa = fields.Many2one('feosco.ward', string='Đến Phường/Xã',
                                domain="[('district_id', '=', feosco_district_id)]")
    address = fields.Char(string='Đến Địa chỉ')
    thoi_gian_xe_toi = fields.Char(string='Thời gian xe tới')
    uoc_tinh_phi_ship = fields.Text(string='Ước tính phí ship')
    note = fields.Text(string='Ghi chú')
    transporter_phone = fields.Char(string='SDT', related='transporter_id.phone_number', store=True, readonly=True)
    transporter_address = fields.Char(string='Address', compute='get_transport_address')

    # @api.onchange('transporter_id')
    # def onchange_transporter(self):
    #     if self.transporter_id:
    #         self.transporter_name = self.transporter_id.name

    @api.depends('transporter_id')
    def get_transport_address(self):
        for record in self:
            if record.transporter_id:
                address = '%s, %s, %s, %s' % (record.transporter_id.address, record.transporter_id.phuong_xa.name,
                                              record.transporter_id.feosco_district_id.name,
                                              record.transporter_id.feosco_city_id.name)
                record.transporter_address = address

    @api.model
    def create(self, vals):
        res = super(tts_transporter_route, self).create(vals)
        feosco_district_id = self.env['feosco.district'].search(
            [('city_id', '=', res.feosco_city_id.id), ('name', '=', res.feosco_district_id.name)], limit=1)
        if feosco_district_id:
            res.feosco_district_id = feosco_district_id
        return res
