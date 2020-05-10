# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class stock_location(models.Model):
    _inherit = 'stock.location'

    not_sellable = fields.Boolean('Not Sellable', default=False)

