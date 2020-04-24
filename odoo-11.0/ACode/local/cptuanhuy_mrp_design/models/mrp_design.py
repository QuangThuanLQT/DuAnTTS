# -*- coding: utf-8 -*-

import time
from dateutil import relativedelta
from datetime import datetime
from odoo import models, fields, api

class cptuanhuy_mrp_design(models.Model):
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name = 'mrp.design'

    name       = fields.Char('Name', required=True)
    date_start = fields.Date('Date Start', require=True, default=lambda x: time.strftime('%Y-%m-01'))
    date_end   = fields.Date('Date End', require=True, default=lambda x: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    line_ids   = fields.One2many('mrp.design.line', 'design_id', 'Design')

class cptuanhuy_mrp_design_line(models.Model):
    _name = 'mrp.design.line'

    design_id  = fields.Many2one('mrp.design', 'Design')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    date = fields.Date('Date Design')
    qty = fields.Integer('Quantity', default=lambda x: 1)
    user_id = fields.Many2one('res.users', 'Designer')