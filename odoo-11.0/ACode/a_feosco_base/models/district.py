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

class feosco_district(models.Model):
    _name = "feosco.district"
    _description = "this is module master district"

    name = fields.Char('Name', size=256,)
    code = fields.Char('Code', size=64,)
    city_id = fields.Many2one('feosco.city', string='City')
    # city_id = fields.Char(string='City')
    sequence = fields.Integer(u'Thứ tự ưu tiên')

    sql_constraints = [
        ('code', 'unique(code)', 'The code must be unique'),
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
