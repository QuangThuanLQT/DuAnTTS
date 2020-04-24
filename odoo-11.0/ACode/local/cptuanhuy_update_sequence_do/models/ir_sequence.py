# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ir_sequence_ihr(models.Model):
    _inherit = 'ir.sequence'

    @api.model
    def update_sequence_do(self):

        # Changes ir sequence
        wh_int_seq = self.env['ir.sequence'].search([('name','=','My Company Sequence internal')])
        for seq in wh_int_seq:
            if seq.prefix == 'WH/INT/':
                seq.prefix = 'CK/INT/'
        wh_in_seq = self.env['ir.sequence'].search([('name', '=', 'My Company Sequence in')])
        for seq in wh_in_seq:
            if seq.prefix == 'WH/IN/':
                seq.prefix = 'NK/IN/'
        wh_out_seq = self.env['ir.sequence'].search([('name', '=', 'My Company Sequence out')])
        for seq in wh_out_seq:
            if seq.prefix == 'WH/OUT/':
                seq.prefix = 'XK/OUT/'

        #Changes sequence in DO

        picking_ids = self.env['stock.picking'].search([])
        for picking_id in picking_ids:
            picking_name = False
            if picking_id.picking_type_id and picking_id.picking_type_id.sequence_id.prefix == 'CK/INT/':
                picking_name = "CK" + picking_id.name[2:]
            if picking_id.picking_type_id and picking_id.picking_type_id.sequence_id.prefix == 'NK/IN/':
                picking_name = "NK" + picking_id.name[2:]
            if picking_id.picking_type_id and picking_id.picking_type_id.sequence_id.prefix == 'XK/OUT/':
                picking_name = "XK" + picking_id.name[2:]
            if picking_name:
                picking_name_dup = self.env['stock.picking'].search([('name','=',picking_name)])
                if not picking_name_dup:
                    picking_id.name = picking_name
