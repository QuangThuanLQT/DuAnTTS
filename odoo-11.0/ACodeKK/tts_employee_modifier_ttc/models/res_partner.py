# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class tts_employee_modifier_ttc(models.Model):
    _inherit = 'res.partner'

    ma_nv = fields.Char(size=4, string='Mã NV')
    is_an_employee = fields.Boolean(help="Check this box if this contact is an Employee.")
    employee_company_id = fields.Many2one('employee.company')
    ma_nv_full = fields.Char(compute='get_ma_nv_full', store=True)

    @api.constrains('ma_nv')
    def check_ma_nv(self):
        for rec in self:
            if rec.ma_nv and rec.employee_company_id:
                exists = self.env['res.partner'].search([('employee_company_id', '=', rec.employee_company_id.id), ('ma_nv', '=', rec.ma_nv), ('id', '!=', rec.id)])
                if exists:
                    raise exceptions.ValidationError("Mã NV Bị Trùng. Xin Vui Lòng Nhập Lại!")

    @api.depends('ma_nv', 'employee_company_id')
    def get_ma_nv_full(self):
        for rec in self:
            if rec.ma_nv and rec.employee_company_id:
                rec.ma_nv_full = 'NV-%s%s' % (rec.employee_company_id.name, rec.ma_nv)