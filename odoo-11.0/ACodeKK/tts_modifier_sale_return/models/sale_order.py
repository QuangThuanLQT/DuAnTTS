# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, datetime
from odoo.exceptions import ValidationError

class sale_order_ihr(models.Model):
    _inherit = 'sale.order'

    reason_cancel = fields.Many2one('reason.cancel.sale', string='Lý do', copy=False)
    trang_thai_dh = fields.Selection([
        ('waiting_pick', 'Waiting to Pick'), ('ready_pick', 'Ready to Pick'), ('picking', 'Picking'),
        ('waiting_pack', 'Waiting to Pack'), ('packing', 'Packing'),
        ('waiting_delivery', 'Waiting to Delivery'), ('delivery', 'Delivering'),
        ('reveive', 'Receive'), ('waiting', 'Waiting to Check'), ('checking', 'Checking'),
        ('done', 'Done'),
        ('reverse_tranfer', 'Reverse Tranfer'),
        ('cancel', 'Cancelled')
    ], string='Trạng thái đơn hàng', compute='_get_trang_thai_dh', store=True)
    check_show_cancel = fields.Boolean(compute='_get_show_cancel')
    return_type = fields.Selection([('all', 'Trả hàng toàn phần'), ('part', 'Trả hàng một phần')],
                                   string='Cách thức trả hàng')
    receive_method = fields.Selection(
        [('warehouse', 'Nhận hàng trả lại tại kho'),
         ('local', 'Nhận hàng trả lại tại địa chỉ giao hàng')], string='Phương thức nhận hàng')
    location_return = fields.Selection([('normal', 'Kho Bình thường'),
                                        ('damaged', 'Kho hư hỏng')], string='Kho lưu trữ sản phẩm', default='normal')
    so_tien_da_tra = fields.Float(string='Số tiền đã trả')
    con_phai_tra = fields.Float(string='Số tiền còn phải trả', compute='_con_phai_tra')
    user_create_return = fields.Many2one('res.users')
    sale_return_state = fields.Selection([('draft', 'Draft'), ('sale_order', 'Order Return'), ('cancel', 'Cancel')],
                                         compute='get_sale_return_state')
    sale_set_draft_id = fields.Many2one('sale.order', copy=False)
    total_quantity = fields.Float(string='Tổng số lượng', compute='_get_total_quantity')
    confirm_user_id = fields.Many2one('res.users')
    sale_return_cancel = fields.Boolean(default=False, copy=False)

    @api.depends('order_line')
    def _get_total_quantity(self):
        for rec in self:
            total_quantity = 0
            for line in rec.order_line:
                total_quantity += line.product_uom_qty
            rec.total_quantity = total_quantity

    @api.multi
    def get_sale_return_state(self):
        for rec in self:
            if rec.state in ('draft', 'sent', 'waiting'):
                rec.sale_return_state = 'draft'
            elif rec.state in ('sale', 'done'):
                rec.sale_return_state = 'sale_order'
            else:
                rec.sale_return_state = 'cancel'

    @api.multi
    def _con_phai_tra(self):
        for rec in self:
            rec.con_phai_tra = rec.amount_total - rec.so_tien_da_tra

    def _check_show_button_return(self):
        for record in self:
            if (record.picking_ids.filtered(lambda p: p.state != 'cancel') and record.invoice_ids.filtered(
                    lambda inv: inv.state != 'cancel')) or record.state != 'draft':
                record.check_show_button_return = True
            else:
                record.check_show_button_return = False

    @api.multi
    def _get_show_cancel(self):
        for order in self:
            if not order.sale_order_return:
                order.check_show_cancel = False
                if not order.picking_ids:
                    if order.reason_cancel:
                        order.check_show_cancel = True
                    else:
                        order.check_show_cancel = False
                else:
                    if order.reason_cancel:
                        order.check_show_cancel = True
                    else:
                        picking_ids = order.picking_ids.filtered(
                            lambda p: p.state != 'cancel' and not p.is_picking_return and not p.have_picking_return)
                        delivery_id = picking_ids.filtered(lambda l: l.check_is_delivery == True)
                        if delivery_id and all(pick.state == 'done' for pick in delivery_id):
                            order.check_show_cancel = True
                        picking_ids = order.picking_ids.filtered(lambda p: p.state != 'cancel')
                        interl_id = picking_ids.filtered(lambda l: l.is_internal_transfer)
                        if interl_id and all(pick.state == 'done' for pick in interl_id):
                            order.check_show_cancel = True
            else:
                order.check_show_cancel = False
                if not order.picking_ids:
                    if order.reason_cancel:
                        if order.sale_return_state == 'cancel':
                            order.check_show_cancel = True
                        else:
                            order.check_show_cancel = False
                    else:
                        order.check_show_cancel = False
                else:
                    picking_ids = order.picking_ids.filtered(
                        lambda p: p.state != 'cancel' and not p.is_picking_return and not p.have_picking_return)
                    delivery_id = picking_ids.filtered(lambda l: l.check_is_delivery == True)
                    if delivery_id and all(pick.state == 'done' for pick in delivery_id):
                        order.check_show_cancel = True
                    picking_ids = order.picking_ids.filtered(lambda p: p.state != 'cancel')
                    interl_id = picking_ids.filtered(lambda l: l.is_internal_transfer)
                    if interl_id and all(pick.state == 'done' for pick in interl_id):
                        order.check_show_cancel = True
                    if order.sale_return_state == 'cancel':
                        order.check_show_cancel = True

    @api.multi
    def _get_trang_thai_dh(self):

        for rec in self:
            if rec.reason_cancel and not rec.sale_order_return:
                if rec.picking_ids and any(picking.state not in ('done', 'cancel') for picking in
                                           rec.picking_ids):
                    rec.trang_thai_dh = 'reverse_tranfer'
                else:
                    if rec.sale_order_return == False:
                        rec.trang_thai_dh = 'cancel'
                    if not rec.sale_order_return == False:
                        if any(picking.state != 'done' for picking in
                               rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')):
                            pick_ids = rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')
                            if 'reveive' in pick_ids.mapped('receipt_state'):
                                rec.trang_thai_dh = 'reveive'

                        elif any(pack.state != 'done' for pack in
                                 rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)):
                            pack_ids = rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)
                            if 'checking' in pack_ids.mapped('internal_transfer_state'):
                                rec.trang_thai_dh = 'checking'
                            else:
                                rec.trang_thai_dh = 'checking'
                        else:
                            if all(picking.state == 'done' for picking in rec.picking_ids):
                                rec.trang_thai_dh = 'done'

            elif rec.picking_ids:
                if not rec.sale_order_return:
                    if any(picking.state != 'done' for picking in
                           rec.picking_ids.filtered(lambda line: line.check_is_pick == True)):
                        pick_ids = rec.picking_ids.filtered(lambda line: line.check_is_pick == True)
                        if 'waiting_pick' in pick_ids.mapped('state_pick'):
                            rec.trang_thai_dh = 'waiting_pick'
                        elif 'ready_pick' in pick_ids.mapped('state_pick'):
                            rec.trang_thai_dh = 'ready_pick'
                        elif 'picking' in pick_ids.mapped('state_pick'):
                            rec.trang_thai_dh = 'picking'
                    elif any(pack.state != 'done' for pack in
                             rec.picking_ids.filtered(lambda line: line.check_is_pack == True)):
                        pack_ids = rec.picking_ids.filtered(lambda line: line.check_is_pack == True)
                        if 'waiting_pack' in pack_ids.mapped('state_pack'):
                            rec.trang_thai_dh = 'waiting_pack'
                        elif 'packing' in pack_ids.mapped('state_pack'):
                            rec.trang_thai_dh = 'packing'
                    else:
                        delivery_ids = rec.picking_ids.filtered(lambda r: r.check_is_delivery == True)
                        if 'done' in delivery_ids.mapped('state_delivery'):
                            rec.trang_thai_dh = 'done'
                        elif 'waiting_delivery' in delivery_ids.mapped('state_delivery'):
                            rec.trang_thai_dh = 'waiting_delivery'
                        elif 'delivery' in delivery_ids.mapped('state_delivery'):
                            rec.trang_thai_dh = 'delivery'
                else:
                    if any(picking.state != 'done' for picking in
                           rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')):
                        pick_ids = rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')
                        if 'reveive' in pick_ids.mapped('receipt_state'):
                            rec.trang_thai_dh = 'reveive'
                        elif 'cancel' in pick_ids.mapped('receipt_state'):
                            rec.trang_thai_dh = 'cancel'

                    elif any(pack.state != 'done' for pack in
                             rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)):
                        pack_ids = rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)
                        if 'checking' in pack_ids.mapped('internal_transfer_state'):
                            rec.trang_thai_dh = 'checking'
                        else:
                            rec.trang_thai_dh = 'checking'
                    else:
                        if all(picking.state == 'done' for picking in rec.picking_ids):
                            rec.trang_thai_dh = 'done'

    @api.multi
    def action_draft(self):
        for rec in self:
            sale_data = rec.copy_data({})[0]
            if rec.sale_order_return:
                sale_data.update({
                    'reason_cancel' : rec.reason_cancel.id,
                })
            sale_id = self.env['sale.order'].create(sale_data)
            rec.sale_set_draft_id = sale_id
            if rec.sale_order_return:
                action = self.env.ref('sale_purchase_returns.sale_order_return_action').read()[0]
                action['views'] = [[self.env.ref('sale.view_order_form').id, 'form']]
                action['res_id'] = sale_id.id
                return action
            else:
                action = self.env.ref('sale.action_orders').read()[0]
                action['views'] = [[self.env.ref('sale.view_order_form').id, 'form']]
                action['res_id'] = sale_id.id
                return action
    @api.multi
    def action_sale_cancel(self):
        for rec in self:
            action = self.env.ref('tts_modifier_sale_return.sale_cancel_popup_action').read()[0]
            action['context'] = {'default_order_id': rec.id}
            return action

    @api.onchange('sale_order_return_ids')
    def _onchange_sale_order_return_ids(self):
        self.order_line = None
        for line in self.sale_order_return_ids.mapped('order_line'):
            if line.product_id not in self.order_line.mapped('product_id'):
                self.order_line += self.order_line.new({
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'price_unit': line.price_unit,
                    'tax_sub': line.tax_sub,
                    'discount': line.discount,
                    'product_uom': line.product_uom,
                    'price_discount': line.price_discount,
                    'product_uom_qty': 0,
                })

    @api.multi
    def button_action_return(self):
        self.state = 'sale'
        self.confirmation_date = fields.Datetime.now()

        for line in self.order_line:
            line.date_order = self.date_order
            if not line.order_id.procurement_group_id:
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)

        if not self.picking_ids.filtered(lambda p: p.state != 'cancel'):
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)

            location_id = False
            location_dest_id = False
            if picking_type_id:
                if picking_type_id.default_location_src_id:
                    location_id = picking_type_id.default_location_src_id.id
                elif self.partner_id:
                    location_id = self.partner_id.property_stock_customer.id
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
                'origin': self.name,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'check_return_picking': True,
                'min_date': self.date_order,
            })

            picking_line = []
            for line in self.order_line:
                if line.product_id or line.quantity != 0:
                    price_unit = 0
                    if self.sale_order_return_ids and self.sale_order_return_ids.mapped('picking_ids'):
                        stock_move = self.sale_order_return_ids.mapped('picking_ids').mapped('move_lines').filtered(
                            lambda ml: ml.product_id == line.product_id)
                        stock_quants = stock_move.mapped('quant_ids')
                        amount = 0
                        qty = 0
                        for stock_quant in stock_quants:
                            amount += stock_quant.inventory_value
                            qty += qty
                        if amount == 0 or qty == 0:
                            price_unit = 0
                        else:
                            price_unit = amount / qty
                    price_unit = price_unit or line.product_id.standard_price
                    picking_line.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': location_id,
                        'location_dest_id': location_dest_id,
                        'picking_type_id': picking_type_id.id,
                        'name': line.product_id.display_name,
                        'group_id': self.procurement_group_id.id or False,
                        'procure_method': 'make_to_stock',
                        'warehouse_id': picking_type_id.warehouse_id.id,
                        'origin': self.name,
                        'price_unit': price_unit,
                        'date': self.date_order,
                    }))

            picking_id.write({'move_lines': picking_line})
            picking_id.action_confirm()
            picking_id.force_assign()
            if self.sale_order_return_ids and all(sale_order.picking_ids for sale_order in self.sale_order_return_ids):
                picking_order_ids = self.sale_order_return_ids.mapped('picking_ids').filtered(
                    lambda p: p.state != 'done')
                if not picking_order_ids:
                    picking_id.action_assign()
            if not self.sale_order_return_ids:
                picking_id.action_assign()
            picking_id.min_date = self.date_order
        # Sale return
        self.confirmation_date = fields.Datetime.now()
        self.user_create_return = self._uid
        self.confirm_user_id = self._uid
        picking_ids = self.env['stock.picking'].search(
            [('group_id', '=', self.procurement_group_id.id)]) if self.procurement_group_id else []
        if picking_ids:
            picking_id = picking_ids.filtered(lambda p: p.is_internal_transfer)
            if self.location_return == 'damaged':
                location_not_sellable_id = self.env['stock.location'].search(
                    [('usage', '=', 'internal'), ('not_sellable', '=', True)], limit=1)
                if location_not_sellable_id:
                    picking_id.location_dest_id = location_not_sellable_id
                    for line in picking_id.move_lines:
                        line.location_dest_id = location_not_sellable_id
                picking_ids.write({
                    'kho_luu_tru': 'error',
                })
            picking_ids.write({
                'check_return_picking': True,
            })
            picking_ids.force_assign()

    @api.constrains('sale_order_return_ids', 'order_line')
    def constrains_sale_order_return_lines(self):
        if self.sale_order_return and self.sale_order_return_ids:
            sale_return_ids = self.env['sale.order'].search(
                [('sale_order_return_ids', 'in', self.sale_order_return_ids.id), ('sale_return_cancel', '=', False)])
            for line in self.order_line:
                if line.product_id:
                    order_line = self.sale_order_return_ids.mapped('order_line').filtered(
                        lambda l: l.product_id.id == line.product_id.id)
                    order_return_line = sale_return_ids.mapped('order_line').filtered(
                        lambda l: l.product_id.id == line.product_id.id)
                    product_uom_qty = sum(order_line.mapped('product_uom_qty')) - sum(
                        order_return_line.mapped('product_uom_qty'))
                    if product_uom_qty < 0:
                        raise ValidationError(
                            _("Tổng số lượng sp %s trả lại  không thể lớn hơn %s." % (line.product_id.name, sum(order_line.mapped('product_uom_qty')))))

    @api.multi
    def write(self, vals):
        res = super(sale_order_ihr, self).write(vals)
        if not self._context.get('non_update',False):
            for rec in self:
                for line in rec.order_line:
                    if line.product_uom_qty <= 0:
                        line.with_context({'non_update' : True}).unlink()
        return res


class sale_order_line_ihr(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'product_uom_qty')
    def onchange_product_uom_qty(self):
        if self.sale_order_return == True and 'sale_order_ctx' in self._context and self._context.get('sale_order_ctx'):
            sale_id = self.env['sale.order'].browse(self._context.get('sale_order_ctx')[0][2])
            sale_return_ids = self.env['sale.order'].search([('sale_order_return_ids', 'in', sale_id.id),('sale_return_cancel', '=', False)])
            if self.product_id:
                order_line = sale_id.mapped('order_line').filtered(lambda l: l.product_id.id == self.product_id.id)
                order_return_line = sale_return_ids.mapped('order_line').filtered(
                    lambda l: l.product_id.id == self.product_id.id)
                product_uom_qty = sum(order_line.mapped('product_uom_qty')) - sum(
                    order_return_line.mapped('product_uom_qty'))
                if product_uom_qty < 0:
                    self.product_uom_qty = 0
                    return {
                        'warning': {
                            'title': "Warning",
                            'message': "Tổng số lượng sp %s trả lại không thể lớn hơn %s." % (
                            self.product_id.name, sum(order_line.mapped('product_uom_qty'))),
                        }
                    }


