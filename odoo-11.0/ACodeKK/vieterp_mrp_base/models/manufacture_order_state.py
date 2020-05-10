# -*- coding: utf-8 -*-

from odoo import models, fields, api

class manufacture_order_state(models.Model):
    _name = 'manufacture.order.state'

    name  = fields.Char('Name')
    code  = fields.Char('Code')