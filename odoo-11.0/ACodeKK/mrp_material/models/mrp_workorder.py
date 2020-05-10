# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mrp_workorder(models.Model):
    _inherit = 'mrp.workorder'

    material_request_ids = fields.One2many('mrp.material.request', 'workorder_id', 'Request Materials')
    material_return_ids = fields.One2many('mrp.material.return', 'workorder_id', 'Return Materials')