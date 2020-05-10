# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class product_product(models.Model):
    _inherit = 'product.product'

    default_code = fields.Char(readonly=False, track_visibility='onchange')

    @api.constrains('default_code')
    def _check_public_holiday(self):
        for rec in self:
            if rec.default_code:
                product_ids = rec.search([('default_code', '=', rec.default_code), ('id', '!=', rec.id)])
                if product_ids:
                    raise ValidationError(_('Mã nội bộ phải là duy nhất!'))
