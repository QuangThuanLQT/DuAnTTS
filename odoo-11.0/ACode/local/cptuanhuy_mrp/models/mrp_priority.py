# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mrp_priority(models.Model):
    _name = 'mrp.priority'

    name = fields.Char('Name')