# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_order(models.Model):
    _inherit = 'sale.order'

    guarantee_ids = fields.One2many('account.guarantee', 'sale_id', 'Guarantees')