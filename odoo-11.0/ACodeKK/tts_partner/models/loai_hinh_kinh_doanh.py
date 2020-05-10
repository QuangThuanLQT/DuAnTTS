# -*- coding: utf-8 -*-

from odoo import models, fields, api

class loai_hinh_kinh_doanh(models.Model):
    _name = 'loai.hinh.kinh.doanh'

    name = fields.Char(string='Loại hình kinh doanh', required=1)
    tax = fields.Selection([('0', '0%'),('5', '5%'),('10', '10%')],string='Thuế GTGT(%)')