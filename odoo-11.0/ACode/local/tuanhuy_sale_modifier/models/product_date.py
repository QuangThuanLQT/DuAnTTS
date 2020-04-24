from odoo import models, fields, api

class product_to_date(models.Model):
    _name = 'product.to.date'

    product_group_id        = fields.Many2many('product.group',string='Product Group')
    band_name_id            = fields.Many2many('brand.name',string='Brand')
    date_number             = fields.Integer('Expired Time')