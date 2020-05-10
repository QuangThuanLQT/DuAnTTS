# -*- coding: utf-8 -*-

from odoo import models, fields, api

class project_task(models.Model):
    _inherit = 'project.task'

    documentation = fields.Char('Documentation')
    so_id = fields.Many2one('sale.order', 'Sale Order')
    so_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')
    bom_id = fields.Many2one('mrp.bom', 'BOM')