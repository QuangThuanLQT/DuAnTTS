# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class product_template(models.Model):
    _inherit = 'product.template'


    def action_create_bom(self):
        ids = self.env.context.get('active_ids', [])
        product_ids = self.browse(ids)
        routing_id = self.env['mrp.routing'].search([('name', '=', 'Tuan Huy')])
        for product in product_ids:
            if product.bom_count < 1:
                self.env['mrp.bom'].create({
                    'product_tmpl_id' : product.id,
                    'product_uom_id'  : product.uom_id.id,
                    'type'            : 'normal',
                    'routing_id'      : routing_id and routing_id.id or False
                })
            else:
                bim_ids = self.env['mrp.bom'].search([('product_tmpl_id', '=', product.id)])
                for bom in bim_ids:
                    if not bom.routing_id and routing_id:
                        bom.routing_id = routing_id
        True