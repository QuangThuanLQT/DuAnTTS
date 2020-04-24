# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class sale_purchase_returns(models.Model):
    _inherit = 'account.invoice'

    check_create_picking = fields.Boolean(string='Create Picking Return')
    picking_ids          = fields.Many2many('stock.picking')
    check_picking_ids    = fields.Integer(compute='_get_check_picking_ids')
    sale_order_id        = fields.Many2one('sale.order', string='Sale Order')
    purchase_order_id    = fields.Many2one('purchase.order', string='Purchase Order')

    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        if self.sale_order_id:
            self.partner_id = self.sale_order_id.partner_id

    @api.onchange('purchase_order_id')
    def onchange_purchase_order_id(self):
        if self.purchase_order_id:
            self.partner_id = self.purchase_order_id.partner_id

    def _get_check_picking_ids(self):
        for record in self:
            record.check_picking_ids = len(record.picking_ids)

    @api.multi
    def action_invoice_open(self):
        for record in self:
            if record.check_create_picking and 'allow_invoice_open' not in self._context:
                product_list = ""
                if record.type == 'out_refund':
                    sale_ids            = self.env['sale.order'].search([
                        ('partner_id', '=', record.partner_id.id),
                        ('state', 'in', ['sale', 'done'])
                    ])
                    product_sale_ids    = sale_ids.mapped('order_line').mapped('product_id')
                    product_invoice_ids = record.invoice_line_ids.mapped('product_id')
                    for product_invoice_id in product_invoice_ids:
                        if product_invoice_id not in product_sale_ids:
                            product_list += product_invoice_id.name + ", "

                if record.type == 'in_refund':
                    sale_ids            = self.env['purchase.order'].search([
                        ('partner_id', '=', record.partner_id.id),
                        ('state', 'in', ['purchase', 'done'])
                    ])
                    product_sale_ids    = sale_ids.mapped('order_line').mapped('product_id')
                    product_invoice_ids = record.invoice_line_ids.mapped('product_id')
                    for product_invoice_id in product_invoice_ids:
                        if product_invoice_id not in product_sale_ids:
                            product_list += product_invoice_id.name + ", "

                if product_list:
                    comment = " không có mua bán các sản phẩm này: "

                    return {
                        'name': 'Warning',
                        'type': 'ir.actions.act_window',
                        'res_model': 'warning.return.picking',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'comment': comment,
                            'invoice_id': record.id,
                            'parnert_name' : record.partner_id.name,
                            'product_list' : product_list,
                        }
                    }
                else:
                    return super(sale_purchase_returns, self).action_invoice_open()
            else:
                return super(sale_purchase_returns, self).action_invoice_open()

    def create_sale_order_return(self):
        sale_order_id = self.env['sale.order'].create({
            'partner_id' : self.partner_id.id,
            'origin'     : self.number,
            'sale_order_return' : True
        })
        data_line = []
        for invoice_line in self.invoice_line_ids:
            data_line.append((0,0,{
                'product_id' : invoice_line.product_id.id,
                'name': invoice_line.product_id.name,
                'product_uom_qty': -invoice_line.quantity,
                'product_uom': invoice_line.uom_id.id,
                'price_unit': invoice_line.price_unit,
                'discount': invoice_line.discount,
                'tax_id': [(6,0,invoice_line.invoice_line_tax_ids.ids)],
                'tax_sub': invoice_line.invoice_line_tax_ids[0].amount or 0,
                'invoice_lines' :[(6,0,invoice_line.ids)],
            }))
        sale_order_id.write({
            'order_line' : data_line
        })

        return sale_order_id

    def create_purchase_order_return(self):
        purchase_order_id = self.env['purchase.order'].create({
            'partner_id' : self.partner_id.id,
            'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'purchase_order_return' : True
        })
        data_line = []
        for invoice_line in self.invoice_line_ids:
            data_line.append((0,0,{
                'product_id' : invoice_line.product_id.id,
                'name': invoice_line.product_id.name,
                'date_planned':datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'product_qty': -invoice_line.quantity,
                'product_uom': invoice_line.uom_id.id,
                'price_unit': invoice_line.price_unit,
                'discount': invoice_line.discount,
                'taxes_id': [(6,0,invoice_line.invoice_line_tax_ids.ids)],
                'tax_sub': invoice_line.invoice_line_tax_ids[0].amount or 0,
                'invoice_lines' :[(6,0,invoice_line.ids)],
            }))
        purchase_order_id.write({
            'order_line' : data_line
        })

        return purchase_order_id

    def create_picking_return(self):
        if self.type == 'out_refund':
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
            if not picking_type_id:
                raise ValidationError('Vui lòng loại tạo  vận chuyển tên: Nhập Kho')
        if self.type == 'in_refund':
            picking_type_id = self.env['stock.picking.type'].search([('name', '=', 'Phiếu Giao Hàng')], limit=1)
            if not picking_type_id:
                raise ValidationError('Vui lòng loại tạo  vận chuyển tên: Phiếu Giao Hàng')

        location_id = False
        location_dest_id = False
        if picking_type_id:
            if picking_type_id.default_location_src_id:
                location_id = picking_type_id.default_location_src_id.id
            elif self.partner_id:
                location_id = self.partner_id.property_stock_supplier.id
            else:
                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

            if picking_type_id.default_location_dest_id:
                location_dest_id = picking_type_id.default_location_dest_id.id
            elif self.partner_id:
                location_dest_id = self.partner_id.property_stock_customer.id
            else:
                location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

        picking_id = self.env['stock.picking'].create({
            'picking_type_id': picking_type_id.id,
            'partner_id': self.partner_id.id,
            'origin': self.number,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
        })

        picking_line = []
        for line in self.invoice_line_ids:
            if line.product_id or line.quantity != 0:
                picking_line.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.uom_id.id,
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                    'name': line.product_id.display_name
                }))

        picking_id.write({'move_lines': picking_line})
        self.picking_ids = [(4, picking_id.id)]
        # if self.type == 'out_refund':
        #     sale_order_id = self.create_sale_order_return()
        #     sale_order_id.action_confirm()
        # if self.type == 'in_refund':
        #     purchase_order_id = self.create_purchase_order_return()
        #     purchase_order_id.button_confirm()
        return picking_id

    def open_picking(self):
        return {
            'name': 'Hoạt động Kho',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.picking_ids.ids)],

        }
