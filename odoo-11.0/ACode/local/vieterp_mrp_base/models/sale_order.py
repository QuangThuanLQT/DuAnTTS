# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sale_order(models.Model):
    _inherit = 'sale.order'

    sale_order_type = fields.Selection([
        ('customize', 'Sản Xuất'),
        ('normal', 'Thương Mại'),
    ], 'Sale Order Type', default='normal')
    routing_id = fields.Many2one('mrp.routing', 'Routing')

    @api.multi
    def action_create_bom(self):
        bom_obj = self.env['mrp.bom']
        for record in self:
            line_index = 0
            for line in record.order_line:
                line_index += 1
                if not line.bom_id or not line.bom_id.id:
                    bom_data = {
                        'product_tmpl_id': line.product_id.product_tmpl_id and line.product_id.product_tmpl_id.id or False,
                        'product_id': line.product_id and line.product_id.id or False,
                        'so_id': record.id,
                        'so_line_id': line.id,
                        'product_qty': 1,
                        'routing_id': record.routing_id and record.routing_id.id or False,
                        'code': '%s-%s' %(record.name, line.product_id.default_code or line.product_id.barcode or line_index),
                        'type': 'normal',
                    }
                    bom = bom_obj.create(bom_data)
                    line.bom_id = bom
