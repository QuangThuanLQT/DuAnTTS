# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'

    wh_print_stock_loc_id = fields.Many2one('stock.location', string='Print Location')
    wh_kcs1_stock_loc_id = fields.Many2one('stock.location', string='KCS1 Location')
    wh_kcs2_stock_loc_id = fields.Many2one('stock.location', string='KCS2 Location')

    produce_name_type_id = fields.Many2one('stock.picking.type', string='Produce Name type')
    produce_image_type_id = fields.Many2one('stock.picking.type', string='Produce Image type')
    print_type_id = fields.Many2one('stock.picking.type', string='Print type')
    kcs1_type_id = fields.Many2one('stock.picking.type', string='KCS1')
    kcs2_type_id = fields.Many2one('stock.picking.type', string='KCS2')

    @api.model
    def create_picking_type(self):
        vals = {}
        warehouse_id = self.search([], limit=1)
        if warehouse_id:
            sub_locations = {
                'wh_print_stock_loc_id': {'name': _('Print'), 'active': True, 'usage': 'internal'},
                'wh_kcs1_stock_loc_id': {'name': _('KSC1'), 'active': True, 'usage': 'internal'},
                'wh_kcs2_stock_loc_id': {'name': _('KSC2'), 'active': True, 'usage': 'internal'},
            }
            for field_name, values in sub_locations.iteritems():
                values['location_id'] = warehouse_id.view_location_id.id
                values['company_id'] = warehouse_id.company_id.id
                vals[field_name] = self.env['stock.location'].with_context(active_test=False).create(values).id
            warehouse_id.write(vals)
            new_vals = warehouse_id.create_sequences_and_picking_types_print()
            warehouse_id.write(new_vals)
        True

    def _get_sequence_values_print(self):
        res = {
            'produce_name_type_id': {'name': self.name + ' ' + _('Sequence produce name'), 'prefix': self.code + '/PRC_NAME/', 'padding': 5},
            'produce_image_type_id': {'name': self.name + ' ' + _('Sequence produce image'), 'prefix': self.code + '/PRC_IMG/', 'padding': 5},
            'print_type_id': {'name': self.name + ' ' + _('Sequence printing'), 'prefix': self.code + '/PRINT/', 'padding': 5},
            'kcs1_type_id': {'name': self.name + ' ' + _('Sequence ksc1'), 'prefix': self.code + '/KSC1/', 'padding': 5},
            'kcs2_type_id': {'name': self.name + ' ' + _('Sequence kcs2'), 'prefix': self.code + '/KSC2/', 'padding': 5},
        }
        return res

    def create_sequences_and_picking_types_print(self):

        IrSequenceSudo = self.env['ir.sequence'].sudo()
        PickingType = self.env['stock.picking.type']

        input_loc, output_loc = self._get_input_output_locations(self.reception_steps, self.delivery_steps)

        # choose the next available color for the picking types of this warehouse
        all_used_colors = [res['color'] for res in
                           PickingType.search_read([('warehouse_id', '!=', False), ('color', '!=', False)], ['color'],
                                                   order='color')]
        available_colors = [zef for zef in [0, 3, 4, 5, 6, 7, 8, 1, 2] if zef not in all_used_colors]
        color = available_colors and available_colors[0] or 0

        # suit for each warehouse: reception, internal, pick, pack, ship
        max_sequence = PickingType.search_read([('sequence', '!=', False)], ['sequence'], limit=1,
                                               order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0

        warehouse_data = {}
        sequence_data = self._get_sequence_values_print()
        # tde todo: backport sequence fix
        create_data = {
            'produce_name_type_id': {
                'name': _('Produce Name Number'),
                'code': 'internal',
                'use_create_lots': True,
                'use_existing_lots': False,
                'default_location_src_id': False,
                'sequence': max_sequence + 1,
            }, 'produce_image_type_id': {
                'name': _('Product Image'),
                'code': 'internal',
                'use_create_lots': False,
                'use_existing_lots': True,
                'default_location_dest_id': False,
                'sequence': max_sequence + 2,
            }, 'print_type_id': {
                'name': _('Print'),
                'code': 'internal',
                'use_create_lots': False,
                'use_existing_lots': True,
                'default_location_src_id': self.wh_print_stock_loc_id.id,
                'sequence': max_sequence + 5,
            }, 'kcs1_type_id': {
                'name': _('KSC1'),
                'code': 'internal',
                'use_create_lots': False,
                'use_existing_lots': True,
                'default_location_src_id': self.wh_kcs1_stock_loc_id.id,
                'sequence': max_sequence + 3,
            }, 'kcs2_type_id': {
                'name': _('KSC2'),
                'code': 'internal',
                'use_create_lots': False,
                'use_existing_lots': True,
                'default_location_src_id': self.wh_kcs2_stock_loc_id.id,
                'sequence': max_sequence + 4,
            },
        }
        # data = self._get_picking_type_values_print(self.reception_steps, self.delivery_steps, self.wh_pack_stock_loc_id)
        # for field_name, values in data.iteritems():
        #     data[field_name].update(create_data[field_name])

        for picking_type, values in create_data.iteritems():
            sequence = IrSequenceSudo.create(sequence_data[picking_type])
            values.update(warehouse_id=self.id, color=color, sequence_id=sequence.id)
            warehouse_data[picking_type] = PickingType.create(values).id

        return warehouse_data
