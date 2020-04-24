# -*- coding: utf-8 -*-

# from odoo import models, fields, api
#
#
# class partner_ihr(models.Model):
#     _inherit = 'res.partner'
#
#     sale_type = fields.Selection([('allow', 'Cho phép kinh doanh'), ('stop', 'Ngừng kinh doanh')], string='Trạng thái',default='allow',
#                                  groups="tts_modifier_access_right.group_giam_doc_kd, tts_modifier_access_right.group_truong_kd")