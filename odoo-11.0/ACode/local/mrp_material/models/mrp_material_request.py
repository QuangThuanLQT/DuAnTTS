# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class mrp_material_request(models.Model):
    _name = 'mrp.material.request'

    production_id = fields.Many2one('mrp.production', string='MO')
    workorder_id = fields.Many2one('mrp.workorder', string='Work Order')
    name = fields.Char('Description', index=True, required=True)
    product_id = fields.Many2one('product.product', 'Product', domain=[('type', 'in', ['product', 'consu'])],
                                 index=True, required=True, states={'done': [('readonly', True)]})
    date_expected = fields.Datetime(
        'Expected Date', default=fields.Datetime.now, index=True, required=True,
        states={'done': [('readonly', True)]},
        help="Scheduled date for the processing of this move")
    date = fields.Datetime(
        'Date', default=fields.Datetime.now, index=True, required=True,
        states={'done': [('readonly', True)]},
        help="Move date: scheduled date until move is done, then date of actual move processing")
    ordered_qty = fields.Float('Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True, states={'done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'), ('confirmed', 'Waiting Availability'),
        ('assigned', 'Available'), ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")