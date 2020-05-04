# -*- coding: utf-8 -*-

from odoo import models, fields, api

class brand_name(models.Model):
    _name = "brand.name"

    name = fields.Char('Thương hiệu')
    tiep_dau_ngu = fields.Char('Tiếp đầu ngữ')

class source_name(models.Model):
    _name = "source.name"

    name = fields.Char('Xuất xứ')