# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _get_wo_state(self):
        result = []
        states = self.env['work.order.state'].sudo().search([])
        for state in states:
            result.append((state.code, state.name))
        return result

    wo_id          = fields.Many2one('mrp.workcenter', 'Workcenter', compute='_compute_mo')
    wo_state       = fields.Selection(_get_wo_state, 'WO State', compute='_compute_mo')
    weight_mo      = fields.Float('Weight MO')
    weight_mo_unit = fields.Many2one('product.uom', 'Weight UOM')
    bom_id         = fields.Many2one('mrp.bom', 'BOM')

    # @api.multi
    # def _compute_bom(self):
    #     for record in self:
    #         if record.order_id:
    #             if record.product_id and record.product_id.product_tmpl_id:
    #                 bom = self.env['mrp.bom'].search([
    #                     # ('so_id', '=', record.order_id.id),
    #                     ('product_tmpl_id', '=', record.product_id.product_tmpl_id.id),
    #                 ], limit=1)
    #                 if bom and bom.id:
    #                     record.bom_id = bom


    @api.multi
    def _compute_mo(self):
        for record in self:
            production = self.env['mrp.production'].search([
                ('so_id', '=', record.order_id.id),
                ('so_line_id', '=', record.id),
            ], limit=1)
            if production and production.id:
                if production.workorder_ids:
                    wc_end = production.workorder_ids[len(production.workorder_ids)-1].id
                    for wo_line in production.workorder_ids:
                        if wo_line.state != 'done' or wc_end == wo_line.id:
                            record.wo_id    = wo_line.workcenter_id
                            record.wo_state = wo_line.state
                            break