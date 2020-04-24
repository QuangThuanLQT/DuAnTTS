# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_order_return(models.Model):
    _name = 'sale.order.return'

    name = fields.Char(string='Reference return')
    don_tra_hang = fields.Boolean(default=False)
    partner_id = fields.Many2one('res.partner', string="Customer")
    sale_order_return_ids = fields.Char(string="Sale Order")
    reason_cancel = fields.Many2one('ly.do.tra.hang', string='Lý do')
    receive_method = fields.Selection(
        [('allow', 'Nhận hàng trả lại tại kho'), ('stop', 'Nhận hàng trả lại tại địa chỉ giao hàng')],
        string="Phương thức nhận hàng")
    location_return = fields.Selection([('allow', 'Kho Bình thường'), ('stop', 'Kho hư hỏng')],
                                       string="Kho lưu trữ sản phẩm")
    note = fields.Text(string='Diễn giải')
    # ...................
    confirmation_date = fields.Datetime(string='Confirmation Date', compute=False, store=True, index=True,
                                        readonly=True, help="Date on which the sales order is confirmed.",
                                        default=fields.Datetime.now)
    so_tien_da_tra = fields.Float(string='Số tiền đã trả')
    con_phai_tra = fields.Float(string='Số tiền còn phải trả')
    trang_thai_tt = fields.Selection(
        [('chua_tt', 'Chưa thanh toán'),
         ('tt_1_phan', 'Thanh toán 1 phần'),
         ('done_tt', 'Hoàn tất thanh toán')],
        string='Trạng thái thanh toán', default='chua_tt', required=1)
    trang_thai_dh = fields.Selection([
        ('waiting_pick', 'Waiting to Pick'), ('ready_pick', 'Ready to Pick'), ('picking', 'Picking'),
        ('waiting_pack', 'Waiting to Pack'), ('packing', 'Packing'),
        ('waiting_delivery', 'Waiting to Delivery'), ('delivery', 'Delivering'),
        ('reveive', 'Receive'), ('waiting', 'Waiting to Check'), ('checking', 'Checking'),
        ('done', 'Done'),
        ('reverse_tranfer', 'Reverse Tranfer'),
        ('cancel', 'Cancelled')
    ], string='Trạng thái đơn hàng', store=True)
    create_uid = fields.Many2one('res.users', 'Created by', index=True, readonly=True)
    confirm_user_id = fields.Many2one('res.users', string='Validate by', readonly=True)
    state_return = fields.Selection([
        ('draft', 'Draft'),
        ('order_return', 'Order Return')], default='draft', string='Status')

    @api.multi
    def order_return(self):
        self.state_return = 'order_return'

    order_line_ids = fields.One2many('order.line', 'order_line_id')

    # tax_id = fields.Char(string='Thuế')
    tax_id = fields.Many2one('account.tax', string='Thuế')
    discount_type = fields.Selection([('percent', 'Tỷ lên phần trăm'), ('amount', 'Số tiền')],
                                     string='Loại giảm giá', default='percent')
    discount_rate = fields.Float('Tỷ lệ chiết khấu')
    check_box_co_cq = fields.Boolean(default=False, string="CO, CQ")
    check_box_invoice_gtgt = fields.Boolean(default=False, string="Invoice GTGT")

    total_quantity = fields.Float(string='Tổng số lượng', readonly=True)
    amount_untaxed = fields.Float(string='Số tiền chưa tính', readonly=True, digits=(16,0))
    amount_tax = fields.Float(string='Thuế', readonly=True, digits=(16,0))
    amount_total = fields.Float(string='Total', readonly=True,digits=(16,0))

    # @api.depends('order_line')
    # def _get_total_quantity(self):
    #     for rec in self:
    #         total_quantity = 0
    #         for line in rec.order_line:
    #             total_quantity += line.product_uom_qty
    #         rec.total_quantity = total_quantity
    #
    # @api.depends('order_line.price_total')
    # def _amount_all(self):
    #     for order in self:
    #         amount_untaxed = amount_tax = 0.0
    #         for line in order.order_line:
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += line.price_tax
    #         order.update({
    #             'amount_untaxed': order.currency_id.round(amount_untaxed),
    #             'amount_tax': order.currency_id.round(amount_tax),
    #             'amount_total': amount_untaxed + amount_tax,
    #         })
    #
    # @api.depends('price_unit', 'product_uom_qty', 'discount')
    # def _compute_amount(self):
    #     for rec in self:
    #         if rec.discount:
    #             disc_amount = (rec.price_unit * rec.product_uom_qty) * rec.discount / 100
    #             rec.price_subtotal = (rec.price_unit * rec.product_uom_qty) - disc_amount
    #         else:
    #             rec.price_subtotal = rec.price_unit * rec.product_uom_qty


    class thong_tin_order_line(models.Model):
        _name = 'order.line'


        order_line_id = fields.Many2one('sale.order.return')
        product_id = fields.Many2one('product.product', string='Sản phẩm')
        invoice_name = fields.Char(string='Tên Hoá Đơn')
        product_uom_qty = fields.Float(string='Số lượng đặt hàng', default=1.0)
        check_box_prinizi_confirm = fields.Boolean(default=False, string="Xác nhận in")
        print_qty = fields.Float(string='Print Qty', digits=(16, 0))
        price_unit = fields.Float(string='Đơn giá', default=0.0)
        price_subtotal = fields.Float(string='Tổng phụ', default=0.0)



        # @api.multi
        # def _con_phai_tra(self):
        #     for rec in self:
        #         rec.con_phai_tra = rec.amount_total - rec.so_tien_da_tra

        # @api.multi
        # def _get_trang_thai_dh(self):
        #
        #     for rec in self:
        #         if rec.reason_cancel and not rec.sale_order_return:
        #             if rec.picking_ids and any(picking.state not in ('done', 'cancel') for picking in
        #                                        rec.picking_ids):
        #                 rec.trang_thai_dh = 'reverse_tranfer'
        #             else:
        #                 if rec.sale_order_return == False:
        #                     rec.trang_thai_dh = 'cancel'
        #                 if not rec.sale_order_return == False:
        #                     if any(picking.state != 'done' for picking in
        #                            rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')):
        #                         pick_ids = rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')
        #                         if 'reveive' in pick_ids.mapped('receipt_state'):
        #                             rec.trang_thai_dh = 'reveive'
        #
        #                     elif any(pack.state != 'done' for pack in
        #                              rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)):
        #                         pack_ids = rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)
        #                         if 'checking' in pack_ids.mapped('internal_transfer_state'):
        #                             rec.trang_thai_dh = 'checking'
        #                         else:
        #                             rec.trang_thai_dh = 'checking'
        #                     else:
        #                         if all(picking.state == 'done' for picking in rec.picking_ids):
        #                             rec.trang_thai_dh = 'done'
        #
        #         elif rec.picking_ids:
        #             if not rec.sale_order_return:
        #                 if any(picking.state != 'done' for picking in
        #                        rec.picking_ids.filtered(lambda line: line.check_is_pick == True)):
        #                     pick_ids = rec.picking_ids.filtered(lambda line: line.check_is_pick == True)
        #                     if 'waiting_pick' in pick_ids.mapped('state_pick'):
        #                         rec.trang_thai_dh = 'waiting_pick'
        #                     elif 'ready_pick' in pick_ids.mapped('state_pick'):
        #                         rec.trang_thai_dh = 'ready_pick'
        #                     elif 'picking' in pick_ids.mapped('state_pick'):
        #                         rec.trang_thai_dh = 'picking'
        #                 elif any(pack.state != 'done' for pack in
        #                          rec.picking_ids.filtered(lambda line: line.check_is_pack == True)):
        #                     pack_ids = rec.picking_ids.filtered(lambda line: line.check_is_pack == True)
        #                     if 'waiting_pack' in pack_ids.mapped('state_pack'):
        #                         rec.trang_thai_dh = 'waiting_pack'
        #                     elif 'packing' in pack_ids.mapped('state_pack'):
        #                         rec.trang_thai_dh = 'packing'
        #                 else:
        #                     delivery_ids = rec.picking_ids.filtered(lambda r: r.check_is_delivery == True)
        #                     if 'done' in delivery_ids.mapped('state_delivery'):
        #                         rec.trang_thai_dh = 'done'
        #                     elif 'waiting_delivery' in delivery_ids.mapped('state_delivery'):
        #                         rec.trang_thai_dh = 'waiting_delivery'
        #                     elif 'delivery' in delivery_ids.mapped('state_delivery'):
        #                         rec.trang_thai_dh = 'delivery'
        #             else:
        #                 if any(picking.state != 'done' for picking in
        #                        rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')):
        #                     pick_ids = rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')
        #                     if 'reveive' in pick_ids.mapped('receipt_state'):
        #                         rec.trang_thai_dh = 'reveive'
        #                     elif 'cancel' in pick_ids.mapped('receipt_state'):
        #                         rec.trang_thai_dh = 'cancel'
        #
        #                 elif any(pack.state != 'done' for pack in
        #                          rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)):
        #                     pack_ids = rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)
        #                     if 'checking' in pack_ids.mapped('internal_transfer_state'):
        #                         rec.trang_thai_dh = 'checking'
        #                     else:
        #                         rec.trang_thai_dh = 'checking'
        #                 else:
        #                     if all(picking.state == 'done' for picking in rec.picking_ids):
        #                         rec.trang_thai_dh = 'done'
