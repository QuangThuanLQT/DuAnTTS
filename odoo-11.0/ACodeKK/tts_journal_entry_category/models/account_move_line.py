# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_move_line_ihr(models.Model):
    _inherit = 'account.move.line'

    group_level_1 = fields.Many2one('journal.entry.category',domain=[('level','=','level_1')], string='Nhóm tài khoản 1',readonly=True)
    group_level_2 = fields.Many2one('journal.entry.category', domain=[('level', '=', 'level_2')], string='Nhóm tài khoản 2',readonly=True)
    group_level_3 = fields.Many2one('journal.entry.category', domain=[('level', '=', 'level_3')], string='Nhóm tài khoản 3',readonly=True)

    @api.onchange('account_id')
    def get_group_level(self):
        for rec in self:
            if rec.account_id:
                rec.group_level_1 = rec.account_id.group_level_1
                rec.group_level_2 = rec.account_id.group_level_2
                rec.group_level_3 = rec.account_id.group_level_3

    @api.model
    def create(self,val):
        rec = super(account_move_line_ihr, self).create(val)
        if not self._context.get('not_base_account',False):
            rec.group_level_1 = rec.account_id.group_level_1
            rec.group_level_2 = rec.account_id.group_level_2
            rec.group_level_3 = rec.account_id.group_level_3
        return rec

    @api.multi
    def write(self,val):
        if 'account_id' in val and not self._context.get('not_base_account',False):
            account_id = self.env['account.account'].browse(val.get('account_id',False))
            if account_id:
                val.update({
                    'group_level_1': account_id.group_level_1.id,
                    'group_level_2': account_id.group_level_2.id,
                    'group_level_3': account_id.group_level_3.id,
                })
        rec = super(account_move_line_ihr, self).write(val)
        return rec



