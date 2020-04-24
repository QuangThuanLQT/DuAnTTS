# -*- coding: utf-8 -*-

from odoo import models, fields, api


class res_partner(models.Model):
    _inherit = 'res.partner'

    delivery_method = fields.Selection(
        [('warehouse', 'Tới kho lấy hàng'),
         ('delivery', 'Giao tới tận nơi'),
         ('transport', 'Giao tới nhà xe'), ], string='Phương thức giao hàng'
    )
    transport_route_id = fields.Many2one('tts.transporter.route', string='Tuyến xe')
    delivery_scope_id = fields.Many2one('tts.delivery.scope', string='Phạm vi giao hàng', compute='_get_delivery_scope')

    @api.depends('transport_route_id', 'feosco_district_id', 'feosco_city_id', 'feosco_ward_id')
    def _get_delivery_scope(self):
        for record in self:
            if record.delivery_method == 'delivery':
                delivery_scope_id = self.env['tts.delivery.scope'].search(
                    [('feosco_district_id', '=', record.feosco_district_id.id),
                     ('feosco_city_id', '=', record.feosco_city_id.id),
                     ('phuong_xa', '=', record.feosco_ward_id.id)], limit=1)
                if delivery_scope_id:
                    record.delivery_scope_id = delivery_scope_id.id
            elif record.delivery_method == 'transport':
                if record.transport_route_id:
                    delivery_scope_id = self.env['tts.delivery.scope'].search(
                        [('feosco_district_id', '=', record.transport_route_id.transporter_id.feosco_district_id.id),
                         ('feosco_city_id', '=', record.transport_route_id.transporter_id.feosco_city_id.id),
                         ('phuong_xa', '=', record.transport_route_id.transporter_id.phuong_xa.id)], limit=1)
                    if delivery_scope_id:
                        record.delivery_scope_id = delivery_scope_id.id

    @api.onchange('delivery_method')
    def onchange_get_delivery_scope(self):
        if self.delivery_method == 'delivery':
            delivery_scope_ids = self.env['tts.delivery.scope'].search(
                [('feosco_city_id', '=', self.feosco_city_id.id),
                 ('feosco_district_id', '=', self.feosco_district_id.id),
                 ('phuong_xa', '=', self.feosco_ward_id.id)])
            if delivery_scope_ids:
                self.delivery_scope_id = delivery_scope_ids[0]
            else:
                self.delivery_scope_id = None
            return {'domain': {'delivery_scope_id': [('id', 'in', delivery_scope_ids.ids)]}}
        elif self.delivery_method == 'transport':
            transport_route_ids = self.env['tts.transporter.route'].search([
                ('feosco_city_id', '=', self.feosco_city_id.id),
                ('feosco_district_id', '=', self.feosco_district_id.id)
            ])
            if transport_route_ids:
                self.transport_route_id = transport_route_ids[0]
            else:
                self.transport_route_id = None
            return {'domain': {'transport_route_id': [('id', 'in', transport_route_ids.ids)]}}
            delivery_scope_ids = self.env['tts.delivery.scope']
            if self.transport_route_id:
                delivery_scope_ids = self.env['tts.delivery.scope'].search(
                    [('feosco_city_id', '=', self.transport_route_id.transporter_id.feosco_city_id.id),
                     ('feosco_district_id', '=', self.transport_route_id.transporter_id.feosco_district_id.id),
                     ('phuong_xa', '=', self.transport_route_id.transporter_id.phuong_xa.id)])
                if delivery_scope_ids:
                    self.delivery_scope_id = delivery_scope_ids[0]