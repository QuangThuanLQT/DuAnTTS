# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import StringIO
import xlsxwriter
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import time


class stock_picking_type_ihr(models.Model):
    _inherit = 'stock.picking.type'

    count_picking_reverse_transfer = fields.Integer(compute='_compute_picking_count')

    @api.multi
    def _compute_picking_count(self):
        kiem_hang_type = self.env.ref('stock.picking_type_internal')
        for rec in self:
            if rec.id == 3:
                True
            # TDE TODO count picking can be done using previous two
            domains = {
                'count_picking_draft': [('state', '=', 'draft')],
                'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
                'count_picking_ready': [('state', 'in', ('assigned', 'partially_available'))],
                'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available'))],
                'count_picking_late': [('min_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                       ('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available'))],
                'count_picking_backorders': [('backorder_id', '!=', False),
                                             ('state', 'in', ('confirmed', 'assigned', 'waiting', 'partially_available'))],
                'count_picking_reverse_transfer' : [('is_picking_return', '=', True)]
            }

            location_pack_zone = self.env.ref('stock.location_pack_zone')
            stock_location_output = self.env.ref('stock.stock_location_output')
            if 'PICK' in rec.sequence_id.prefix or rec.default_location_dest_id == location_pack_zone:
                domains.update({
                    'count_picking_waiting' : [('state_pick', '=', 'waiting_pick'),('is_picking_return', '=', False)],
                    'count_picking_ready' : [('state_pick', 'in', ('ready_pick', 'picking')),('is_picking_return', '=', False)]
                })
            elif 'PACK' in rec.sequence_id.prefix or rec.default_location_src_id == location_pack_zone:
                domains.update({
                    'count_picking_waiting': [('state_pack', '=', 'waiting_another_operation'),('is_picking_return', '=', False)],
                    'count_picking_ready': [('state_pack', 'in', ('waiting_pack','packing')),('is_picking_return', '=', False)]
                })
            elif 'OUT' in rec.sequence_id.prefix and not rec.default_location_src_id:
                domains.update({
                    'count_picking_waiting': [('state_delivery', '=', 'waiting_another_operation'),('is_picking_return', '=', False)],
                    'count_picking_ready': [('state_delivery', 'in', ('waiting_delivery','delivery')),('is_picking_return', '=', False)]
                })
            elif 'IN' in rec.sequence_id.prefix and rec.default_location_src_id == stock_location_output:
                domains.update({
                    'count_picking_reverse_transfer': [('is_picking_return', '=', True)]
                })
            elif rec == kiem_hang_type:
                domains.update({
                    'count_picking_waiting': [('internal_transfer_state', '=', 'waiting_another'), ('is_picking_return', '=', False)],
                    'count_picking_ready': [('internal_transfer_state', 'in', ('waiting','checking')), ('is_picking_return', '=', False)]
                })
            # else:
            #     domains.update({
            #         'count_picking_reverse_transfer': [('is_picking_return', '=', False)]
            #     })

            for field in domains:
                if 'OUT' in rec.sequence_id.prefix and rec.default_location_src_id == stock_location_output:
                    data = self.env['stock.picking'].read_group(domains[field] +
                                                            [('state', '!=', 'cancel'),
                                                             ('picking_type_id', 'in', rec.ids)],
                                                            ['picking_type_id'], ['picking_type_id'])
                else:
                    data = self.env['stock.picking'].read_group(domains[field] +
                                                                [('state', 'not in', ('done', 'cancel')),
                                                                 ('picking_type_id', 'in', rec.ids)],
                                                                ['picking_type_id'], ['picking_type_id'])
                count = dict(
                    map(lambda x: (x['picking_type_id'] and x['picking_type_id'][0], x['picking_type_id_count']), data))
                for record in rec:
                    record[field] = count.get(record.id, 0)
            for record in rec:
                record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
                record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0

    @api.multi
    def get_action_picking_tree_waiting(self):
        action = self.env.ref('stock.action_picking_tree_waiting').read()[0]
        location_pack_zone = self.env.ref('stock.location_pack_zone')
        stock_location_output = self.env.ref('stock.stock_location_output')
        kiem_hang_type = self.env.ref('stock.picking_type_internal')
        if 'PICK' in self.sequence_id.prefix or self.default_location_dest_id == location_pack_zone:
            action['domain'] = [('state_pick', '=', 'waiting_pick'),('state', 'not in', ('done', 'cancel')),('is_picking_return', '=', False)]
        elif 'PACK' in self.sequence_id.prefix or self.default_location_src_id == location_pack_zone:
            action['domain'] = [('state_pack', '=', 'waiting_another_operation'),('state', 'not in', ('done', 'cancel')),('is_picking_return', '=', False)]
        elif 'OUT' in self.sequence_id.prefix and self.default_location_src_id == stock_location_output:
            action['domain'] = [('state_delivery', '=', 'waiting_another_operation'),('state', 'not in', ('done', 'cancel')),('is_picking_return', '=', False)]
        elif self == kiem_hang_type:
            action['domain'] = [('internal_transfer_state', '=', 'waiting_another'),('state', 'not in', ('done', 'cancel')),('is_picking_return', '=', False)]
        if action['domain']:
            action['context'] = {
                'search_default_picking_type_id': [self.id],
                'default_picking_type_id': self.id,
                'contact_display': 'partner_address',
            }
        return action

    @api.multi
    def get_action_picking_tree_ready(self):
        action = self.env.ref('stock.action_picking_tree_ready').read()[0]
        location_pack_zone = self.env.ref('stock.location_pack_zone')
        stock_location_output = self.env.ref('stock.stock_location_output')
        kiem_hang_type = self.env.ref('stock.picking_type_internal')
        if 'PICK' in self.sequence_id.prefix or self.default_location_dest_id == location_pack_zone:
            action['domain'] = [('state_pick', 'in', ('ready_pick', 'picking')),('state', 'not in', ('done', 'cancel')),('is_picking_return', '=', False)]
        elif 'PACK' in self.sequence_id.prefix or self.default_location_src_id == location_pack_zone:
            action['domain'] = [('state_pack', 'in', ('waiting_pack','packing')),('state', 'not in', ('done', 'cancel')),('is_picking_return', '=', False)]
        elif 'OUT' in self.sequence_id.prefix and self.default_location_src_id == stock_location_output:
            action['domain'] = [('state_delivery', 'in', ('waiting_delivery','delivery')),('state', '!=', 'cancel'),('is_picking_return', '=', False)]
        elif self == kiem_hang_type:
            action['domain'] = [('internal_transfer_state', 'in', ('waiting','checking')),('state', 'not in', ('done', 'cancel')),('is_picking_return', '=', False)]
        if action['domain']:
            action['context'] = {
                'search_default_picking_type_id': [self.id],
                'default_picking_type_id': self.id,
                'contact_display': 'partner_address',
            }
        return action

    @api.multi
    def get_action_picking_tree_reserve_transfer(self):
        action = self.env.ref('stock.action_picking_tree_ready').read()[0]
        location_pack_zone = self.env.ref('stock.location_pack_zone')
        stock_location_output = self.env.ref('stock.stock_location_output')
        if 'PICK' in self.sequence_id.prefix or self.default_location_dest_id == location_pack_zone:
            action['domain'] = [('is_picking_return', '=', True),('state', 'not in', ('done', 'cancel'))]
        elif 'PACK' in self.sequence_id.prefix or self.default_location_src_id == location_pack_zone:
            action['domain'] = [('is_picking_return', '=', True),('state', 'not in', ('done', 'cancel'))]
        elif 'OUT' in self.sequence_id.prefix and self.default_location_src_id == stock_location_output:
            action['domain'] = [('is_picking_return', '=', True),('state', 'not in', ('done', 'cancel'))]
        else:
            action['domain'] = [('is_picking_return', '=', True), ('state', 'not in', ('done', 'cancel'))]
        if action['domain']:
            action['context'] = {
                'search_default_picking_type_id': [self.id],
                'default_picking_type_id': self.id,
                'contact_display': 'partner_address',
            }
        return action