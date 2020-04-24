# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Attributes(models.Model):
    _inherit = 'product.attribute'

    type = fields.Selection([('radio', 'Radio'), ('select', 'Select'), ('color', 'Color'), ('hidden', 'Hidden')])


class Atttrbutes_value(models.Model):
    _inherit = 'product.attribute.value'

    html_color = fields.Char(string='HTML Color Index', oldname='color', help="Here you can set a " "specific HTML color index (e.g. #ff0000) to display the color on the website if the "
                                                                              "attibute type is 'Color'.")
