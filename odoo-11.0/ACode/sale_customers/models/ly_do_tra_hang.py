# -*- coding: utf-8 -*-

from odoo import models, fields, api

class lydotrahang(models.Model):
    _name = 'ly.do.tra.hang'

    name = fields.Char(string='Lý do')