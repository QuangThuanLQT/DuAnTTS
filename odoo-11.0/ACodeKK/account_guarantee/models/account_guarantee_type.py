# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_guarantee_type(models.Model):
    _name = 'account.guarantee.type'
    _order = 'id asc'

    name = fields.Char('Guarantee Type')