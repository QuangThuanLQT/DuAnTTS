# -*- coding: utf-8 -*-

from odoo import models, fields, api

class tts_delivery_scope(models.Model):
    _name = 'tts.delivery.scope'

    def _get_default_hcm(self):
        feosco_city_id = self.env['feosco.city'].search([('name','=','Hồ Chí Minh')],limit=1)
        return feosco_city_id.id

    feosco_city_id = fields.Many2one('feosco.city', u'Tỉnh/Thành Phố', required=1,default=_get_default_hcm)
    feosco_district_id = fields.Many2one('feosco.district', u'Quận/Huyện',
                                         domain="[('city_id', '=', feosco_city_id)]", required=1)
    phuong_xa = fields.Many2one('feosco.ward',string='Phường/Xã', domain="[('district_id', '=', feosco_district_id)]",required=1)
    state = fields.Selection([('co_giao','Có giao'),('khong_giao','không giao')],string='Trạng thái', required=1)
    khu_vuc = fields.Selection([('noi_thanh','Nội Thành'),('ngoai_thanh_1','Ngoại Thành 1'),('ngoai_thanh_2','Ngoại Thành 2'),('khong_giao_hang', 'Không giao hàng')], string='Khu vực', required=1)
    phi_giao_hang = fields.Float(string='Phí giao hàng phát sinh')
    thuong_giao_hang = fields.Float(string='Thưởng giao hàng')
    thuong_giao_hang_tang_ca = fields.Float(string='Thưởng giao hàng tăng ca')

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            khu_vuc = dict(self.env['tts.delivery.scope'].fields_get(allfields=['khu_vuc'])['khu_vuc'][
                             'selection'])
            res.append((record.id,"%s" % (khu_vuc.get(record.khu_vuc))))
        return res

    @api.model
    def create(self, vals):
        res = super(tts_delivery_scope, self).create(vals)
        feosco_district_id = self.env['feosco.district'].search(
            [('city_id', '=', res.feosco_city_id.id), ('name', '=', res.feosco_district_id.name)], limit=1)
        if feosco_district_id:
            res.feosco_district_id = feosco_district_id
            phuong_xa = self.env['feosco.ward'].search(
                [('district_id', '=', res.feosco_district_id.id), ('name', '=', res.phuong_xa.name)], limit=1)
            if phuong_xa:
                res.phuong_xa = phuong_xa
        return res