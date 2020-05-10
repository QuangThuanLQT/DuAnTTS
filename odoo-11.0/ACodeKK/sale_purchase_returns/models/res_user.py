# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _

class res_user_inherit(models.Model):
    _inherit = 'res.users'

    ma_bin = fields.Char(string="Mã Pin")