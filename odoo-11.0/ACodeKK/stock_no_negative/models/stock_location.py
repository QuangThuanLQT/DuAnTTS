# -*- coding: utf-8 -*-
# © 2015-2016 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class StockLocation(models.Model):
    _inherit = 'stock.location'

    allow_negative_stock = fields.Boolean(
        string='Allow Negative Stock',
        help="Allow negative stock levels for the stockable products "
        "attached to this category. The options doesn't apply to products "
        "attached to sub-categories of this category.")
