# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ir_sequence(models.Model):
    _inherit = 'ir.sequence'

    def update_sequence_number_next_actual(self):
        ir_sequence_ids = self.env['ir.sequence'].search([('prefix','in',['WH/IN/','WH/INT/','WH/OUT/','PO','SO'])])
        for sequence in ir_sequence_ids:
            sequence.number_next_actual = 1