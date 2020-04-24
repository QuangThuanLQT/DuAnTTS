# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class mrp_bom_inherit(models.Model):
    _inherit = 'mrp.bom'

    so_id = fields.Many2one('sale.order')
    so_line_id = fields.Many2one('sale.order.line')
