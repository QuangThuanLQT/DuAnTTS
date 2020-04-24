# -*- coding: utf-8 -*-

from odoo import fields, models, api

class res_company(models.Model):
    _inherit = "res.company"

    #return default country is Viet Nam
    @api.model
    def _get_country_id(self):
        country = self.env['res.country'].search([('code','=','VN')], limit=1)
        return country.id if country else False

    feosco_district_id = fields.Many2one('feosco.district', string="District")
    feosco_city_id = fields.Many2one('feosco.city', string="City")
    feosco_ward_id = fields.Many2one('feosco.ward', 'Phường/Xã', domain="[('district_id.id', '=', feosco_district_id)]")

    _defaults = {
        'country_id': _get_country_id,
    }