# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_order_ihr(models.Model):
    _inherit = 'sale.order'

    block_reason = fields.Many2one('reason.cancel.sale', string='Nguyên nhân khóa đơn hàng')

    @api.multi
    def action_sale_block(self):
        for rec in self:
            action = self.env.ref('tts_block_sale_order.sale_block_popup_action').read()[0]
            action['context'] = {'default_order_id': rec.id}
            return action

    @api.multi
    def sale_unblock(self):
        for rec in self:
            rec.block_reason = False
            pickings = rec.mapped('picking_ids')
            for r in pickings:
                r.block_reason = False


class sale_block_popup(models.Model):
    _name = 'sale.block.popup'

    name = fields.Many2one('reason.cancel.sale', string='Nguyên nhân khóa đơn hàng')
    order_id = fields.Many2one('sale.order')

    @api.multi
    def action_block(self):
        for rec in self:
            rec.order_id.block_reason = rec.name
            rec.order_id.update_sale_log_block()
            pickings = rec.order_id.mapped('picking_ids')
            for r in pickings:
                r.block_reason = rec.name

class picking_block(models.Model):
    _inherit = 'stock.picking'

    block_reason = fields.Many2one('reason.cancel.sale',string='Nguyên nhân khóa đơn hàng')
    state_pick_sub = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_pick', 'Waiting'),
         ('ready_pick', 'Ready'),
         ('picking', 'Picking'),
         ('done', 'Done'),
         ('cancel', 'Cancel')], related="state_pick",
        string="Pick state")
    state_pack_sub = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_another_operation', 'Waiting another operation'),
         ('waiting_pack', 'Waiting'),
         ('packing', 'Packing'),
         ('done', 'Done'),
         ('cancel', 'Cancel')], related="state_pack",
        string="Pack state")
    state_delivery_sub = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_another_operation', 'Waiting another operation'),
         ('waiting_delivery', 'Waiting'),
         ('delivery', 'Delivering'),
         ('done', 'Done'),
         ('cancel', 'Cancel')],
        related="state_delivery",
        string="Delivery state")

    @api.multi
    def action_blocked(self):
        pass