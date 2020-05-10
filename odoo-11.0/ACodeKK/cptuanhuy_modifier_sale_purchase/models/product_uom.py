# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class product_uom(models.Model):
    _inherit = 'product.uom'

    @api.model
    def create(self, values):
        raise ValidationError(_("Không được phép tạo đơn vị tính!"))
        # result = super(product_uom, self).create(values)
        # return result

    @api.multi
    def write(self, vals):
        raise ValidationError(_("Không được phép sửa đơn vị tính!"))