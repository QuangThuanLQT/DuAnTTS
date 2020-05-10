# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mrp_production(models.Model):
    _inherit = 'mrp.production'

    material_request_ids = fields.One2many('mrp.material.request', 'production_id', 'Request Materials')
    material_return_ids = fields.One2many('mrp.material.return', 'production_id', 'Return Materials')