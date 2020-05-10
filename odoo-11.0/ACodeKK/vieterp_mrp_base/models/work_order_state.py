# -*- coding: utf-8 -*-

from odoo import models, fields, api

class work_order_state(models.Model):
    _name = 'work.order.state'

    name  = fields.Char('Name')
    code  = fields.Char('Code')