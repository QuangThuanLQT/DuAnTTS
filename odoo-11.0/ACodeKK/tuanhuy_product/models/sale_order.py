# -*- coding: utf-8 -*-
from odoo import models, fields, api

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.onchange('product_id')
    def onchange_product_for_ck(self,partner=None):
        for record in self:
            if not record.sale_order_return and record.product_id and record.product_id.product_tmpl_id and ('partner_id' in self._context or partner):
                group_sale_id = record.product_id.product_tmpl_id.group_sale_id
                if 'partner_id' in self._context:
                    partner_id = self.env['res.partner'].search([('id','=',self._context.get('partner_id'))])
                elif partner:
                    partner_id = self.env['res.partner'].search([('id', '=', partner)])
                if group_sale_id:
                    if not group_sale_id.price_type or group_sale_id.price_type == 'list_price':
                        discount = group_sale_id.group_line_ids.filtered(lambda x: x.partner_id == partner_id or x.partner_name.upper() in partner_id.name.upper() if x.partner_name else False)
                        if discount:
                            record.discount = discount[0].discount
                        else:
                            string = unicode("Ngoài những khách hàng đã lk", "utf-8")
                            discount = group_sale_id.group_line_ids.filtered(lambda x: x.partner_name == string) and group_sale_id.group_line_ids.filtered(lambda x: x.partner_name == string).discount or group_sale_id.group_line_ids and group_sale_id.group_line_ids[0].discount or 0
                            record.discount = discount
                    else:
                        discount = group_sale_id.group_line_ids.filtered(lambda x: x.partner_id == partner_id or x.partner_name.upper() in partner_id.name.upper() if x.partner_name else False)
                        price_unit = sum(record.product_id.mapped(group_sale_id.price_type))
                        if discount:
                            # price_unit = price_unit * (100 + discount[0].discount) / 100
                            record.price_unit = price_unit
                            record.discount = -discount[0].discount
                        else:
                            string = unicode("Ngoài những khách hàng đã lk", "utf-8")
                            discount = group_sale_id.group_line_ids.filtered(
                                lambda x: x.partner_name == string) and group_sale_id.group_line_ids.filtered(
                                lambda x: x.partner_name == string).discount or group_sale_id.group_line_ids and group_sale_id.group_line_ids[0].discount or 0
                            # price_unit = price_unit * (100 + discount) / 100
                            record.price_unit = price_unit
                            record.discount = -discount

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id_for_ck(self):
        partner_name = self.partner_id and self.partner_id.name
        for record in self.order_line:
            if record.product_id and record.product_id.product_tmpl_id:
                group_sale_id = record.product_id.product_tmpl_id.group_sale_id
                if group_sale_id:
                    discount = group_sale_id.group_line_ids.filtered(lambda x: x.partner_id == self.partner_id or x.partner_name in partner_name)
                    if discount:
                        record.discount = discount[0].discount
                    else:
                        string = unicode("Ngoài những khách hàng đã lk", "utf-8")
                        discount = group_sale_id.group_line_ids.filtered(
                            lambda x: x.partner_name == string) and group_sale_id.group_line_ids.filtered(
                            lambda x: x.partner_name == string).discount or group_sale_id.group_line_ids[0].discount
                        record.discount = discount