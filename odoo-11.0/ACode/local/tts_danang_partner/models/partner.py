# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class res_partner(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char(track_visibility='onchange')

    @api.constrains('ref')
    def _check_ref_partner(self):
        for r in self:
            if r.ref:
                exists = self.env['res.partner'].search(
                    [('ref', '=', r.ref), ('id', '!=', r.id)])
                if exists:
                    raise exceptions.ValidationError("Mã KH Nội Bộ Bị Trùng. Xin Vui Lòng Nhập Lại!")
