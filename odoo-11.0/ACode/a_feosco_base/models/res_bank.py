# -*- coding: utf-8 -*-

from odoo import fields, models, api


class res_partner_bank(models.Model):
    _inherit = "res.partner.bank"

    city_id = fields.Many2one('feosco.city', 'City', domain="[('country_id.code', '=', 'VN')]")
    feosco_district_id = fields.Many2one('feosco.district', 'District', domain="[('city_id.id', '=', city_id)]")
    feosco_ward_id = fields.Many2one('feosco.ward', 'Phường/Xã', domain="[('district_id.id', '=', feosco_district_id)]")
    bank_partner_id = fields.Many2one('res.partner', string="Bank", domain="[('bank','=',True)]")
    fullname = fields.Char('Full name')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for record in self:
            if record.partner_id:
                part = record.partner_id
                record.owner_name = part.name
                record.street = part.street or False
                record.feosco_district_id = part.feosco_district_id.id or False
                record.city_id = part.feosco_city_id.id or False
                record.zip = part.zip or False
                record.country_id = part.country_id.id
                record.state_id = part.state_id.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
