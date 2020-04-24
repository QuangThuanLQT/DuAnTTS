# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class stock_picking_ihr(models.Model):
    _inherit = 'stock.picking'

    sale_order_merge = fields.Boolean(string='Đơn gộp', readonly=1, compute='get_so_merge')
    sale_order_merge_ids = fields.Many2one('sale.order',string='Đơn hàng gộp', readonly=1, compute='get_so_merge')

    @api.multi
    def get_so_merge(self):
        for rec in self:
            if rec.sale_id:
                if rec.sale_id.sale_order_merge:
                    rec.sale_order_merge = True
                if rec.sale_id.sale_order_parent_id:
                    rec.sale_order_merge = True
                    rec.sale_order_merge_ids = rec.sale_id.sale_order_parent_id

    @api.multi
    def delivery_action_assign(self):
        for rec in self:
            if rec.sale_order_merge:
                if rec.sale_order_merge_ids:
                    delivery_picking = rec.sale_order_merge_ids.picking_ids.filtered(lambda p: p.check_is_delivery == True)
                    if any(picking.state_delivery in ('draft','waiting_another_operation','waiting_delivery') for picking in delivery_picking):
                        raise UserError(_('Cần xác nhận giao hàng đơn hàng cha.'))
                    else:
                        return super(stock_picking_ihr, self).delivery_action_assign()
                else:
                    sale_order_merge_ids = rec.sale_id.sale_order_merge_ids
                    delivery_picking = sale_order_merge_ids.mapped('picking_ids').filtered(lambda p: p.check_is_delivery == True)
                    if all(picking.state_delivery == 'waiting_delivery' for picking in delivery_picking):
                        raise UserError(_('Còn phiếu giao hàng của đơn hàng con chưa sẳn sàng.'))
                    else:
                        return super(stock_picking_ihr, self).delivery_action_assign()
            else:
                return super(stock_picking_ihr, self).delivery_action_assign()

class stock_picking_type_ihr(models.Model):
    _inherit = 'stock.picking.type'

    # @api.multi
    # def get_action_picking_tree_waiting(self):
    #     action = self.env.ref('stock.action_picking_tree_waiting').read()[0]
    #     location_pack_zone = self.env.ref('stock.location_pack_zone')
    #     stock_location_output = self.env.ref('stock.stock_location_output')
    #     if 'PICK' in self.sequence_id.prefix or self.default_location_dest_id == location_pack_zone:
    #         action['domain'] = [('state_pick', '=', 'waiting_pick'), ('state', 'not in', ('done', 'cancel')),
    #                             ('is_picking_return', '=', False)]
    #     elif 'PACK' in self.sequence_id.prefix or self.default_location_src_id == location_pack_zone:
    #         action['domain'] = [('state_pack', '=', 'waiting_another_operation'),
    #                             ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
    #     elif 'OUT' in self.sequence_id.prefix and self.default_location_src_id == stock_location_output:
    #         print "picking delivery"
    #         action = self.env.ref('prinizi_merge_sale_order.action_picking_delivery_tree_waiting').read()[0]
    #         action['domain'] = [('state_delivery', '=', 'waiting_another_operation'),
    #                             ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
    #     elif self.picking_type == 'internal_sale':
    #         action = self.env.ref('prinizi_merge_sale_order.stock_picking_internal_sale_action_picking_type').read()[0]
    #         action['domain'] = [('internal_sale_type', '=', 'draft'), ('state', '!=', 'cancel'),
    #                             ('is_picking_return', '=', False)]
    #     if action['domain']:
    #         action['context'] = {
    #             'search_default_picking_type_id': [self.id],
    #             'default_picking_type_id': self.id,
    #             'contact_display': 'partner_address',
    #         }
    #     return action

    # @api.multi
    # def get_action_picking_tree_ready(self):
    #     action = self.env.ref('stock.action_picking_tree_ready').read()[0]
    #     location_pack_zone = self.env.ref('stock.location_pack_zone')
    #     stock_location_output = self.env.ref('stock.stock_location_output')
    #     if 'PICK' in self.sequence_id.prefix or self.default_location_dest_id == location_pack_zone:
    #         action['domain'] = [('state_pick', '=', 'ready_pick'), ('state', 'not in', ('done', 'cancel')),
    #                             ('is_picking_return', '=', False)]
    #     elif 'PACK' in self.sequence_id.prefix or self.default_location_src_id == location_pack_zone:
    #         action['domain'] = [('state_pack', 'in', ('waiting_pack', 'packing')),
    #                             ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
    #     elif 'OUT' in self.sequence_id.prefix and self.default_location_src_id == stock_location_output:
    #         action = self.env.ref('prinizi_merge_sale_order.action_picking_delivery_tree_waiting').read()[0]
    #         action['domain'] = [('state_delivery', 'in', ('waiting_delivery', 'delivery')), ('state', '!=', 'cancel'),
    #                             ('is_picking_return', '=', False)]
    #     elif self.picking_type == 'internal_sale':
    #         action = self.env.ref('prinizi_merge_sale_order.stock_picking_internal_sale_action_picking_type').read()[0]
    #         action['domain'] = [('internal_sale_type', '=', 'ready'), ('state', '!=', 'cancel'),
    #                             ('is_picking_return', '=', False)]
    #     if action['domain']:
    #         action['context'] = {
    #             'search_default_picking_type_id': [self.id],
    #             'default_picking_type_id': self.id,
    #             'contact_display': 'partner_address',
    #         }
    #     return action
    #
    # @api.multi
    # def get_action_picking_tree_reserve_transfer(self):
    #     action = self.env.ref('stock.action_picking_tree_ready').read()[0]
    #     location_pack_zone = self.env.ref('stock.location_pack_zone')
    #     stock_location_output = self.env.ref('stock.stock_location_output')
    #     if 'PICK' in self.sequence_id.prefix or self.default_location_dest_id == location_pack_zone:
    #         action['domain'] = [('is_picking_return', '=', True), ('state', 'not in', ('done', 'cancel'))]
    #     elif 'PACK' in self.sequence_id.prefix or self.default_location_src_id == location_pack_zone:
    #         action['domain'] = [('is_picking_return', '=', True), ('state', 'not in', ('done', 'cancel'))]
    #     elif 'OUT' in self.sequence_id.prefix and self.default_location_src_id == stock_location_output:
    #         action = self.env.ref('prinizi_merge_sale_order.action_picking_delivery_tree_waiting').read()[0]
    #         action['domain'] = [('is_picking_return', '=', True), ('state', 'not in', ('done', 'cancel'))]
    #     else:
    #         action['domain'] = [('is_picking_return', '=', True), ('state', 'not in', ('done', 'cancel'))]
    #     if action['domain']:
    #         action['context'] = {
    #             'search_default_picking_type_id': [self.id],
    #             'default_picking_type_id': self.id,
    #             'contact_display': 'partner_address',
    #         }
    #     return action
    #
    # @api.multi
    # def get_stock_picking_action_picking_type(self):
    #     stock_location_output = self.env.ref('stock.stock_location_output')
    #     if 'OUT' in self.sequence_id.prefix and self.default_location_src_id == stock_location_output:
    #         return self._get_action('prinizi_merge_sale_order.stock_picking_delivery_action_picking_type')
    #     elif self.picking_type == 'internal_sale':
    #         return self._get_action('prinizi_merge_sale_order.stock_picking_internal_sale_action_picking_type')
    #     else:
    #         return self._get_action('stock.stock_picking_action_picking_type')


