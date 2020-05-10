# -*- coding: utf-8 -*-

from odoo import models, fields, api

class stock_picking_type(models.Model):
    _inherit = 'stock.picking.type'

    picking_type = fields.Selection([('pick', 'Pick'),
                                     ('pack', 'Pack'),
                                     ('delivery', 'Delivery'),
                                     ('reciept', 'Receipt'),
                                     ('internal', 'Internal'),
                                     ('produce_name', 'Produce Name'),
                                     ('produce_image', 'Produce Image'),
                                     ('print', 'Print'),
                                     ('kcs1', 'KCS1'),
                                     ('kcs2', 'KCS2'),
                                     ('internal_sale', 'Internal Sale'),
                                     ], string='Type')

    @api.multi
    def get_action_picking_tree_waiting(self):
        action = self.env.ref('stock.action_picking_tree_waiting').read()[0]
        if self.picking_type == 'internal_sale':
            action = self.env.ref('prinizi_sale_process.stock_picking_internal_sale_action_picking_type').read()[0]
            action['domain'] = [('internal_sale_type', '=', 'draft'), ('state', '!=', 'cancel'),
                                ('is_picking_return', '=', False)]
        elif self.picking_type == 'produce_name':
            action['domain'] = [('produce_name_state', '=', ('waiting_produce')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'produce_image':
            action['domain'] = [('produce_image_state', '=', ('waiting_produce')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'print':
            action['domain'] = [('print_state', '=', ('waiting_print')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'kcs1':
            action['domain'] = [('kcs1_state', '=', ('waiting')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'kcs2':
            action['domain'] = [('kcs2_state', '=', ('waiting')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        if action['domain']:
            action['context'] = {
                'search_default_picking_type_id': [self.id],
                'default_picking_type_id': self.id,
                'contact_display': 'partner_address',
            }
            return action
        else:
            return super(stock_picking_type, self).get_action_picking_tree_waiting()

    @api.multi
    def get_action_picking_tree_ready(self):
        if self.picking_type == 'internal_sale':
            action = self.env.ref('prinizi_sale_process.stock_picking_internal_sale_action_picking_type').read()[0]
            action['domain'] = [('internal_sale_type', '=', 'ready'), ('state', '!=', 'cancel'),
                                ('is_picking_return', '=', False)]
            if action['domain']:
                action['context'] = {
                    'search_default_picking_type_id': [self.id],
                    'default_picking_type_id': self.id,
                    'contact_display': 'partner_address',
                }
            return action
        elif self.picking_type == 'internal':
            action = self.env.ref('prinizi_sale_process.stock_picking_internal_sale_action_picking_type').read()[0]
            action['domain'] = [('internal_transfer_state', 'in', ('waiting','checking')), ('state', '!=', 'cancel'),
                                ('is_picking_return', '=', False)]
            if action['domain']:
                action['context'] = {
                    'search_default_picking_type_id': [self.id],
                    'default_picking_type_id': self.id,
                    'contact_display': 'partner_address',
                }
            return action
        else:
            return super(stock_picking_type, self).get_action_picking_tree_ready()

    @api.multi
    def get_stock_picking_action_picking_type(self):
        if self.picking_type == 'internal_sale':
            return self._get_action('prinizi_sale_process.stock_picking_internal_sale_action_picking_type')
        else:
            return super(stock_picking_type, self).get_stock_picking_action_picking_type()

