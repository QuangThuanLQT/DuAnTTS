# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from lxml import etree
from odoo.exceptions import ValidationError

class stock_move(models.Model):
    _inherit = 'stock.move'


    location_id = fields.Many2one('stock.location', required=False )
    location_dest_id = fields.Many2one( 'stock.location', required=False)
    picking_type = fields.Selection([('pick', 'Pick'),
                                     ('pack', 'Pack'),
                                     ('delivery', 'Delivery'),
                                     ('reciept', 'Receipt'),
                                     ('internal', 'Internal'),
                                     ('produce_name', 'Produce Name'),
                                     ('produce_image', 'Produce Image'),
                                     ('print', 'Print'),
                                     ('kcs1', 'KCS1'),
                                     ('kcs2', 'KCS2'),
                                     ('internal_sale', 'Internal Sale'),
                                     ], string='Type', related='picking_type_id.picking_type')
    internal_sale_price = fields.Float(string='Đơn giá')
    internal_sale_sub_total = fields.Float(string='Thành tiền', compute='onchange_get_value_sub_total', store=True)
    partner = fields.Char(string="Partners", compute='ref_user')

    @api.multi
    def ref_user(self):
        for rec in self:
            rec.partner = rec.picking_id.partner_id.name or rec.picking_id.user_internal_sale.name

    @api.depends('origin', 'inventory_id')
    def get_move_origin_sub(self):
        for record in self:
            if record.inventory_id:
                record.origin_sub = record.inventory_id.name
            if record.picking_type_id.picking_type == 'internal_sale':
                record.origin_sub = 'Bán nội bộ'
            else:
                record.origin_sub = record.origin

    def check_stock_move_in_out(self):
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        stock_location_suppliers = self.env.ref('stock.stock_location_suppliers')
        stock_location_customers = self.env.ref('stock.stock_location_customers')
        stock_location_scrapped = self.env.ref('stock.stock_location_scrapped')
        location_inventory = self.env.ref('stock.location_inventory')
        location_procurement = self.env.ref('stock.location_procurement')

        not_sellable = self.env['stock.location'].search([('not_sellable', '=', True)])

        if (self.location_id == location_procurement and self.location_dest_id == stock_location_stock) or \
                (self.location_id == location_procurement and self.location_dest_id in not_sellable) or \
                (self.location_id == location_inventory and self.location_dest_id == stock_location_stock) or \
                (self.location_id == location_inventory and self.location_dest_id in not_sellable):
            return 'in'
        elif self.location_dest_id in [stock_location_scrapped,location_inventory,stock_location_customers] or self.picking_type_id.picking_type == 'internal_sale':
            return 'out'
        else:
            return 'dont_know'

    @api.onchange('product_id')
    def onchange_get_value_price(self):
        for rec in self:
            if rec.product_id:
                rec.internal_sale_price = rec.product_id.lst_price

    @api.depends('internal_sale_price','product_uom_qty')
    def onchange_get_value_sub_total(self):
        for rec in self:
            rec.internal_sale_sub_total = rec.internal_sale_price * rec.product_uom_qty

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(stock_move, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree':
            default_picking_type_id = self._context.get('default_picking_type_id', False)
            if default_picking_type_id:
                picking_type = self.env['stock.picking.type'].browse(default_picking_type_id)
                if picking_type.picking_type == 'internal_sale':
                    doc = etree.XML(res['arch'])
                    for node in doc.xpath("//field[@name='internal_sale_price']"):
                        node.set('invisible', '0')
                        node.set('modifiers', """{"tree_invisible": false}""")
                    for node in doc.xpath("//field[@name='internal_sale_sub_total']"):
                        node.set('invisible', '0')
                        node.set('modifiers', """{"tree_invisible": false}""")
                    for node in doc.xpath("//field[@name='location_id']"):
                        node.set('invisible', '1')
                        node.set('modifiers', """{"tree_invisible": true}""")
                    for node in doc.xpath("//field[@name='location_dest_id']"):
                        node.set('invisible', '1')
                        node.set('modifiers', """{"tree_invisible": true}""")
                    res['arch'] = etree.tostring(doc)
        return res

    @api.constrains('product_id', 'product_uom_qty')
    def internal_sale_check_product_qty(self):
        for record in self:
            if record.product_id and record.picking_type == 'internal_sale':
                if record.product_uom_qty > (record.product_id.sp_co_the_ban + record.product_uom_qty):
                    raise ValidationError(
                        _('Bạn định bán %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                            record.product_uom_qty, record.product_id.display_name,
                            record.product_id.sp_co_the_ban + record.product_uom_qty)))

class product_product_ihr(models.Model):
    _inherit = 'product.product'

    @api.depends('qty_available', 'virtual_available')
    def _compute_product(self):
        move_obj = self.env['stock.move'].sudo()
        dest_location = self.env.ref('stock.stock_location_customers')
        for rec in self:
            if self._context.get('location', False):
                sp_ban_chua_giao = sum(move_obj.search(
                    [('product_id', '=', rec.id), ('location_id', '=', self._context.get('location', False)),
                     ('state', 'not in', ['done', 'cancel'])]).mapped('product_uom_qty'))
                move_cancel_ids = move_obj.search(
                    [('product_id', '=', rec.id), ('location_id', '=', self._context.get('location', False)),
                     ('state', '=', 'cancel')])
            else:
                sp_ban_chua_giao = sum(move_obj.search(
                    [('product_id', '=', rec.id), ('location_dest_id', '=', dest_location.id or False),
                     ('state', 'not in', ['done', 'cancel'])]).mapped('product_uom_qty'))
                move_cancel_ids = move_obj.search(
                    [('product_id', '=', rec.id), ('location_dest_id', '=', dest_location.id or False),
                     ('state', '=', 'cancel')])
            sp_ban_da_huy = 0
            for move_cancel_id in move_cancel_ids:
                if move_cancel_id.picking_id.sale_id and move_cancel_id.picking_id.sale_id.trang_thai_dh == 'reverse_tranfer':
                    sp_ban_da_huy += move_cancel_id.product_uom_qty
                if move_cancel_id.picking_id.purchase_id and move_cancel_id.picking_id.purchase_id.operation_state == 'reverse_tranfer':
                    sp_ban_da_huy += move_cancel_id.product_uom_qty

            rec.sp_ban_chua_giao = sp_ban_chua_giao + sp_ban_da_huy

            internal_sale_line = move_obj.search([('product_id', '=', rec.id),('picking_type_id.picking_type', '=', 'internal_sale'),('state', 'not in', ['done','cancel'])])
            line_ids = self.env['sale.order.line'].search(
                [('product_id', '=', rec.id), ('order_id.state', 'in', ('draft', 'sent'))])
            line_purchase_ids = self.env['purchase.order.line'].search(
                [('product_id', '=', rec.id), ('order_id.state', 'in', ('draft', 'sent')),
                 ('order_id.purchase_order_return', '=', True)])
            sp_da_bao_gia = sum(line_ids.mapped('product_uom_qty')) + sum(line_purchase_ids.mapped('product_qty'))
            rec.sp_da_bao_gia = sp_da_bao_gia
            rec.sp_co_the_ban = rec.qty_available - rec.sp_ban_chua_giao - rec.sp_da_bao_gia - sum(internal_sale_line.mapped('product_uom_qty'))

    @api.multi
    def get_pp_stock_move_open(self):
        for record in self:
            stock_location = self.env.ref('stock.stock_location_stock').id
            stock_location_customers = self.env.ref('stock.stock_location_customers').id
            stock_location_scrapped = self.env.ref('stock.stock_location_scrapped').id
            location_inventory = self.env.ref('stock.location_inventory').id
            stock_location_suppliers = self.env.ref('stock.stock_location_suppliers').id
            not_sellable = self.env['stock.location'].search([('not_sellable', '=', True)])
            location_dest_list = [stock_location, stock_location_customers, stock_location_scrapped, location_inventory,
                                  stock_location_suppliers] + not_sellable.ids
            moves = self.env['stock.move'].search(
                [('state', '=', 'done'), ('product_id', '=', record.id)])

            moves_return = self.env['stock.move'].search(
                [('id', 'in', moves.ids), ('picking_id.is_picking_return', '=', True)])

            moves = (moves - moves_return).filtered(lambda m: m.location_dest_id.id in location_dest_list or m.picking_type_id.picking_type == 'internal_sale')

            record.product_stock_move_open = moves
