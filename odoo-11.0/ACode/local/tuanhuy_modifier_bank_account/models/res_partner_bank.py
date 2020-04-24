# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, fields):
        res = super(ResPartnerInherit, self).default_get(fields)
        if 'partner_type' in self._context and self._context.get('partner_type',False) == 'bank':
            res['bank'] = True
            res['customer'] = False
        return res