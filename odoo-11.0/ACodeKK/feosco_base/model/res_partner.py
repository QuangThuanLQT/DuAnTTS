# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, api

class res_partner(models.Model):
    _name = "res.partner"
    _inherit="res.partner"

    @api.model
    def _get_default_country_id(self):
        search_country = [('code', '=', 'VN')]
        country = self.env['res.country'].search(search_country, limit=1)
        return country.id if country else False

    @api.onchange('country_id')
    def event_country_change(self):
        if self.country_id:
            self.city = None
            self.district_id = None

    @api.onchange('city')
    def event_city_change(self):
        if self.city:
            self.feosco_district_id = None
        else:
            return {}

    feosco_city_id = fields.Many2one('feosco.city', u'Thành phố')
    feosco_district_id = fields.Many2one('feosco.district', u'Quận (huyện)', domain="[('city_id', '=', feosco_city_id)]")
    feosco_ward_id = fields.Many2one('feosco.ward', 'Phường/Xã', domain="[('district_id.id', '=', feosco_district_id)]")
    feosco_birthday = fields.Date(u'Sinh nhật')
    feosco_business_license = fields.Char(u'Giấy phép kinh doanh', size=128)
    feosco_business_type = fields.Char(u'Loại hình kinh doanh')
    country_id = fields.Many2one('res.country', u'Quốc gia', domain="[('code', '=', 'VN')]", default=_get_default_country_id)