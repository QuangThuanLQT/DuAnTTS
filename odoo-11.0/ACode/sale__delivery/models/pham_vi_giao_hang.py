# -*- coding: utf-8 -*-

from odoo import models, fields, api


class phamvigiaohang(models.Model):
    _name = 'pham.vi.giao.hang'

    feosco_city_id = fields.Char(string='Tỉnh/Thành Phố', required=1)
    feosco_district_id = fields.Char(string='Quận/Huyện', required=1)
    phuong_xa = fields.Char(string='Phường/Xã', required=1)
    state = fields.Selection([('co_giao', 'Có giao'), ('khong_giao', 'không giao')], string='Trạng thái', required=1)
    khu_vuc = fields.Selection(
        [('noi_thanh', 'Nội Thành'), ('ngoai_thanh_1', 'Ngoại Thành 1'), ('ngoai_thanh_2', 'Ngoại Thành 2'),
         ('khong_giao_hang', 'Không giao hàng')], string='Khu vực', required=1)
    phi_giao_hang = fields.Float(string='Phí giao hàng phát sinh')
    thuong_giao_hang = fields.Float(string='Thưởng giao hàng')
    thuong_giao_hang_tang_ca = fields.Float(string='Thưởng giao hàng tăng ca')

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            khu_vuc = dict(self.env['pham.vi.giao.hang'].fields_get(allfields=['khu_vuc'])['khu_vuc'][
                             'selection'])
            res.append((record.id,"%s" % (khu_vuc.get(record.khu_vuc))))
        return res

