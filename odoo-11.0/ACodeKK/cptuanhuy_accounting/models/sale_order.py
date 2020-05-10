# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sale_order(models.Model):
    _inherit = 'sale.order'

    move_line_ids   = fields.One2many('account.move.line', 'sale_id', string='Account Moves')
    move_line_count = fields.Integer(string='Profit & Lost', compute='_get_profit_and_lost_count')

    def _get_profit_and_lost_count(self):
        for record in self:
            record.move_line_count = len(record.move_line_ids.ids)

    @api.multi
    def action_open_profit_and_lost(self):
        self.ensure_one()

        move_line_ids = self.move_line_ids  # .filtered(lambda ct: ct.is_project == True)
        action = self.env.ref('cptuanhuy_accounting.account_move_pnl_report_action').read()[0]
        action['domain'] = [('id', 'in', move_line_ids.ids)]
        action['context'] = {
            'default_sale_id': self.id,
            'search_default_632': True,
            'search_default_511': True,
            'search_default_641': True,
            'search_default_642': True,
            'search_default_811': True,
            'search_default_622': True,
            'search_default_627': True,
            'pnl_from_sale'     : True
        }
        return action

    @api.multi
    def action_open_phan_bo_mo(self):

        mo_ids = []
        procurement_group_ids = self.procurement_group_id
        picking_ids = self.env['stock.picking'].search([('sale_select_id', '=', self.id)])
        procurement_picking_ids = picking_ids.mapped('move_lines').mapped('procurement_id').ids
        procurement_ids = self.env['procurement.order'].search(['|', ('group_id', 'in', procurement_group_ids.ids), ('id', 'in', procurement_picking_ids)])
        for procurement_id in procurement_ids:
            mo_id = self.env['mrp.production'].search([('procurement_ids', '=', procurement_id.id)])
            if mo_id:
                mo_ids.append(mo_id.id)
        production_ids = self.env['mrp.production'].search([('origin', 'like', '%' + self.name + '%')])
        for record in production_ids:
            if record.id not in mo_ids:
                mo_ids.append(record.id)

        phan_bo_list = []
        phan_bo_ids = self.env['account.move.line'].search([('mrp_production_id', 'in', mo_ids)])
        for record in phan_bo_ids:
            if record.id not in phan_bo_ids:
                phan_bo_list.append(record.id)

        action = self.env.ref('cptuanhuy_accounting.account_action_phan_bo_mo').read()[0]
        action['domain'] = [('id', 'in', phan_bo_ids.ids)]
        return action