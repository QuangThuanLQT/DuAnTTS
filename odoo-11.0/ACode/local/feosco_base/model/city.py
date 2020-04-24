# -*- coding: utf-8 -*-

from odoo import fields, models, api

class feosco_city(models.Model):

    _name = "feosco.city"
    _description = "this is module master city"

    @api.model
    def _get_country_id(self):
        countries = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        return countries.id if countries else False

    name = fields.Char('Name', size=256)
    code = fields.Char('Code', size=64)
    country_id = fields.Many2one('res.country', string='Country', domain="[('code', '=', 'VN')]", default='_get_country_id')
    sequence = fields.Integer(u'Thứ tự ưu tiên')
    
    sql_constraints = [
        ('name', 'unique(name)', 'The key must be unique'),
        ('code', 'unique(code)', 'The code must be unique'),
    ]
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
