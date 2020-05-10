# -*- coding: utf-8 -*-

from odoo import models, fields, api

class tts_journal_entry_category(models.Model):
    _name = 'journal.entry.category'

    name = fields.Char(string='Tên nhóm tài khoản',required=1)
    level = fields.Selection([('level_1','Level 1'),('level_2','Level 2'),('level_3','Level 3')])
    active = fields.Boolean(default=True, string="Lưu trữ")

    @api.multi
    def toggle_active(self):
        for rec in self:
            rec.active = not rec.active