# -*- coding: utf-8 -*-

from odoo import models, fields, api

class hr_attendance_inherit(models.Model):
    _inherit = 'hr.attendance'

    location_in = fields.Char(readonly=1)
    mac_address_in = fields.Char(readonly=1)
    device_info_in = fields.Text(readonly=1)

    location_out = fields.Char(readonly=1)
    mac_address_out = fields.Char(readonly=1)
    device_info_out= fields.Text(readonly=1)