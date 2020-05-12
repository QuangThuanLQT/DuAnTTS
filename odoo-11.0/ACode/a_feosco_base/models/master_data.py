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
import os
import json
import xlrd

class feosco_master_data(models.Model):
    _name = "feosco.master.data"
    _description = "Master data for all feosco modules"

    name = fields.Char('Name', size=256)
    code = fields.Char('Code', size=256)
    type = fields.Char('Type', size=256)

    sql_constraints = [
        ('name', 'unique(name)', 'The key must be unique'),
        ('code', 'unique(code)', 'The code must be unique')
    ]
