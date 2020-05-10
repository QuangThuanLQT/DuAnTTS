# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import time


class stock_picking_type(models.Model):
    _inherit = 'stock.picking.type'

    @api.multi
    def get_action_picking_tree_ready(self):
        action = self.env.ref('stock.action_picking_tree_ready').read()[0]
        location_pack_zone = self.env.ref('stock.location_pack_zone')
        stock_location_output = self.env.ref('stock.stock_location_output')
        if self.picking_type == 'pick':
            action['domain'] = [('state_pick', 'in', ('ready_pick', 'picking')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'pack':
            action['domain'] = [('state_pack', 'in', ('waiting_pack', 'packing')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'delivery':
            action['domain'] = [('state_delivery', 'in', ('waiting_delivery', 'delivery')),
                                ('state', '!=', 'cancel'), ('is_picking_return', '=', False)]
        elif self.picking_type == 'internal_sale':
            action['domain'] = [('internal_sale_type', '=', 'ready'), ('state', '!=', 'cancel'),
                                ('is_picking_return', '=', False)]
        elif self.picking_type == 'produce_name':
            action['domain'] = [('produce_name_state', 'in', ('ready_produce', 'produce')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'produce_image':
            action['domain'] = [('produce_image_state', 'in', ('ready_produce', 'produce')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'print':
            action['domain'] = [('print_state', 'in', ('ready_print', 'print')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'kcs1':
            action['domain'] = [('kcs1_state', '=', ('ready')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]
        elif self.picking_type == 'kcs2':
            action['domain'] = [('kcs2_state', '=', ('ready')),
                                ('state', 'not in', ('done', 'cancel')), ('is_picking_return', '=', False)]

        if action['domain']:
            action['context'] = {
                'search_default_picking_type_id': [self.id],
                'default_picking_type_id': self.id,
                'contact_display': 'partner_address',
            }
        return action

    @api.multi
    def _compute_picking_count(self):
        for rec in self:
            if rec.id == 10:
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
                                             ('state', 'in',
                                              ('confirmed', 'assigned', 'waiting', 'partially_available'))],
                'count_picking_reverse_transfer': [('is_picking_return', '=', True)]
            }

            location_pack_zone = self.env.ref('stock.location_pack_zone')
            stock_location_output = self.env.ref('stock.stock_location_output')
            if rec.picking_type == 'pick':
                domains.update({
                    'count_picking_waiting': [('state_pick', '=', 'waiting_pick'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('state_pick', 'in', ('ready_pick', 'picking')),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'pack':
                domains.update({
                    'count_picking_waiting': [('state_pack', '=', 'waiting_another_operation'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('state_pack', 'in', ('waiting_pack', 'packing')),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'internal_sale':
                domains.update({
                    'count_picking_waiting': [('internal_sale_type', '=', 'draft'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('internal_sale_type', '=', 'ready'),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'delivery':
                domains.update({
                    'count_picking_waiting': [('state_delivery', '=', 'waiting_another_operation'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('state_delivery', 'in', ('waiting_delivery', 'delivery')),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'produce_name':
                domains.update({
                    'count_picking_waiting': [('produce_name_state', '=', 'waiting_produce'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('produce_name_state', 'in', ('ready_produce', 'produce')),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'produce_image':
                domains.update({
                    'count_picking_waiting': [('produce_image_state', '=', 'waiting_produce'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('produce_image_state', 'in', ('ready_produce', 'produce')),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'print':
                domains.update({
                    'count_picking_waiting': [('print_state', '=', 'waiting_print'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('print_state', 'in', ('ready_print', 'print')),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'kcs1':
                domains.update({
                    'count_picking_waiting': [('kcs1_state', '=', 'waiting'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('kcs1_state', '=', ('ready')),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'kcs2':
                domains.update({
                    'count_picking_waiting': [('kcs2_state', '=', 'waiting'),
                                              ('is_picking_return', '=', False)],
                    'count_picking_ready': [('kcs2_state', '=', ('ready')),
                                            ('is_picking_return', '=', False)]
                })
            elif rec.picking_type == 'internal':
                domains.update({
                    'count_picking_waiting': [('internal_transfer_state', '=', 'waiting_another'), ('is_picking_return', '=', False)],
                    'count_picking_ready': [('internal_transfer_state', 'in', ('waiting','checking')), ('is_picking_return', '=', False)]
                })

            elif 'IN' in rec.sequence_id.prefix and rec.default_location_src_id == stock_location_output:
                domains.update({
                    'count_picking_reverse_transfer': [('is_picking_return', '=', True)]
                })

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
