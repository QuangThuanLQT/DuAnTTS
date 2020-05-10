# -*- coding: utf-8 -*-

from odoo import models, fields, api

class attendances_config(models.Model):
    _name = 'attendances.config'

    name = fields.Char(string='MAC address', required=1)
    location_name = fields.Char(string='Location')