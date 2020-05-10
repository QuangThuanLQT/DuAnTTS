# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    validate_date = fields.Date(compute='get_validate_date', store=True)
    validate_weeked = fields.Integer(compute='get_validate_date', store=True)
    validate_month = fields.Integer(compute='get_validate_date', store=True)
    product_category_id = fields.Many2one('product.category', compute='get_product_category', store=True)

    @api.depends('inventory_id.validate_date')
    def get_validate_date(self):
        for rec in self:
            if rec.inventory_id.validate_date:
                rec.validate_date = rec.inventory_id.validate_date
                rec.validate_month = datetime.strptime(rec.inventory_id.validate_date, DEFAULT_SERVER_DATETIME_FORMAT).month
                rec.validate_weeked = datetime.strptime(rec.inventory_id.validate_date, DEFAULT_SERVER_DATETIME_FORMAT).isocalendar()[1]

    @api.depends('product_id')
    def get_product_category(self):
        for rec in self:
            if rec.product_id and rec.product_id.categ_id:
                product_category_id = parent_id = rec.product_id.categ_id
                while parent_id:
                    parent_id = parent_id.parent_id
                    if parent_id:
                        product_category_id = parent_id
                rec.product_category_id = product_category_id


