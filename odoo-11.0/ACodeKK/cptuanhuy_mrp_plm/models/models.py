# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class cptuanhuy_mrp_plm(models.Model):
#     _name = 'cptuanhuy_mrp_plm.cptuanhuy_mrp_plm'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100