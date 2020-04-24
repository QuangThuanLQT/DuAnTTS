# -*- coding: utf-8 -*-

from odoo import models, fields, api

class hr_holidays_status_ihr(models.Model):
    _inherit = 'hr.holidays.status'

    name_sub = fields.Char(string='Tên loại lương', required=1 )

    @api.multi
    def name_get(self):
        res = []
        for field in self:
            res.append((field.id, '%s' % (field.name_sub or field.name)))
        return res
