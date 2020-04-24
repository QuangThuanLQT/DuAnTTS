# -*- coding: utf-8 -*-

from odoo import models, fields, api


class attachment(models.Model):
    _name = 'sale.attachment'

    name = fields.Char()
