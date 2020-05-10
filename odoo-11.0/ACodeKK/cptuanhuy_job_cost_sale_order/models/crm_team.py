# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class crm_team(models.Model):
    _inherit = 'crm.team'

    sequence_id = fields.Many2one('ir.sequence', 'Sequence')