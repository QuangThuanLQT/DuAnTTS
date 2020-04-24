# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_move(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order')

    @api.model
    def create(self, values):
        res = super(account_move, self).create(values)
        return res

    @api.multi
    def update_name_of_je(self):
        account_ids = self.env['account.account'].sudo().search([]).filtered(lambda rec : rec.code.startswith('111') or rec.code.startswith('112'))
        move_line_ids = self.env['account.move.line'].sudo().search([('account_id','in',account_ids.ids)])
        for line in move_line_ids:
            if line.credit == sum(line.move_id.line_ids.mapped('debit')) or line.debit == sum(line.move_id.line_ids.mapped('credit')):
                line.write({'name': ', '.join(line.move_id.line_ids.sorted('id').filtered(lambda rec: rec.id != line.id).mapped('name'))})