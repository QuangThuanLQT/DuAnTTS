# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_account_ihr(models.Model):
    _inherit = 'account.account'

    group_level_1 = fields.Many2one('journal.entry.category',domain=[('level','=','level_1')], context="{'default_level' : 'level_1'}", string='Nhóm tài khoản 1')
    group_level_2 = fields.Many2one('journal.entry.category', domain=[('level', '=', 'level_2')], context="{'default_level' : 'level_2'}", string='Nhóm tài khoản 2')
    group_level_3 = fields.Many2one('journal.entry.category', domain=[('level', '=', 'level_3')], context="{'default_level' : 'level_3'}", string='Nhóm tài khoản 3')
    name_sub = fields.Char(compute='get_name_code_sub', string='Tên')
    code_sub = fields.Char(compute='get_name_code_sub', string='Mã')

    @api.multi
    def get_name_code_sub(self):
        for rec in self:
            parent_id = rec.parent_id
            space = ''
            while parent_id:
                space += "___"
                parent_id = parent_id.parent_id
            rec.name_sub = space + rec.name
            rec.code_sub = space + rec.code