# -*- coding: utf-8 -*-
from openerp import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    purchase_request = fields.Boolean(string='Purchase Request', help="Check this box to generate "
        "purchase request instead of generating requests for quotation from procurement.", default=False)

ProductTemplate()