# -*- coding: utf-8 -*-

from odoo import models, fields, api


class res_users(models.Model):
    _inherit = 'res.users'

    parent_user_id = fields.Many2one('res.users', string="Parent User", compute='compute_child_user')
    is_children = fields.Boolean('Is Child', compute='compute_child_user')
    child_users_ids = fields.Many2many('res.users', 'parent_child_user_rel', 'parent_id', 'child_id', string='Child Users')

    @api.multi
    def compute_child_user(self):
        for record in self:
            parent_id = self.env['res.users'].search([('child_users_ids', '=', record.id)], limit=1)
            if parent_id:
                record.parent_user_id = parent_id
                record.is_children = True
