# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class sale_order_return(models.Model):
    _name = 'sale.order.return'

    name = fields.Char(string='Reference return', readonly=True, required=True, copy=False, default='New')
    don_tra_hang = fields.Boolean(default=False)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True, copy=False)
    # sale_order_return_ids = fields.Char(string="Sale Order")
    sale_order_return_ids = fields.Many2one('sale.order', string="Sale Order", domain="[('partner_id', '=', partner_id)]")
    reason_cancel = fields.Many2one('ly.do.tra.hang', string='Lý do')
    receive_method = fields.Selection(
        [('allow', 'Nhận hàng trả lại tại kho'), ('stop', 'Nhận hàng trả lại tại địa chỉ giao hàng')],
        string="Phương thức nhận hàng", readonly=True)
    location_return = fields.Selection([('allow', 'Kho Bình thường'), ('stop', 'Kho hư hỏng')],
                                       string="Kho lưu trữ sản phẩm")
    note = fields.Text(string='Diễn giải')
    # ...................
    confirmation_date = fields.Datetime(string='Confirmation Date', compute=False, store=True, index=True,
                                        readonly=True, help="Date on which the sales order is confirmed.",
                                        default=fields.Datetime.now)
    so_tien_da_tra = fields.Float(string='Số tiền đã trả')
    con_phai_tra = fields.Float(string='Số tiền còn phải trả', compute='_con_phai_tra')
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
    # ----------------------chuyển sô tiền qua string

    total_text = fields.Char('Total Text', compute='_compute_total')

    @api.multi
    def _compute_total(self):
        for record in self:
            subtotal = record.amount_total
            total_text = self.env['stock.picking'].DocTienBangChu(subtotal)
            record.total_text = total_text


    @api.onchange('sale_order_return_ids')
    def onchange_sale_order_return_ids(self):
        if self.sale_order_return_ids:
            for line in self.sale_order_return_ids.order_line:
                self.order_line_ids += self.order_line_ids.new({
                    'product_id' : line.product_id.id,
                    'invoice_name': line.product_id.name,
                    'price_unit': line.price_unit,
                    'amount_tax': line.tax_id,
                    # 'discount': line.discount,
                    'product_uom': line.product_uom,
                    # 'price_discount': line.price_discount,
                    'product_uom_qty': 0,
                })

    @api.multi
    def order_return(self):
        self.state_return = 'order_return'

    # ...................
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.order.return') or 'New'
        result = super(sale_order_return, self).create(vals)
        return result

    # ...................
    @api.multi
    def _con_phai_tra(self):
        for rec in self:
            rec.con_phai_tra = rec.amount_total - rec.so_tien_da_tra

    order_line_ids = fields.One2many('order.line', 'order_line_id')

    # tax_id = fields.Char(string='Thuế')
    tax_id = fields.Many2one('account.tax', string='Thuế')
    discount_type = fields.Selection([('percent', 'Tỷ lên phần trăm'), ('amount', 'Số tiền')],
                                     string='Loại giảm giá', default='percent')
    discount_rate = fields.Float('Tỷ lệ chiết khấu')
    check_box_co_cq = fields.Boolean(default=False, string="CO, CQ")
    check_box_invoice_gtgt = fields.Boolean(default=False, string="Invoice GTGT")

    total_quantity = fields.Float(string='Tổng số lượng', compute='_get_total_quantity', readonly=True, digits=(16,0))
    amount_untaxed = fields.Float(string='Untaxed Amount', compute='_untax_amount', readonly=True, digits=(16,0))
    amount_tax = fields.Float(string='Taxes',readonly=True, digits=(16,0))
    amount_total = fields.Float(string='Total',compute='_amount_all', readonly=True,digits=(16,0))

    @api.depends('order_line_ids.product_uom_qty')
    def _get_total_quantity(self):
        for rec in self:
            total_quantity = 0
            for line in rec.order_line_ids:
                total_quantity += line.product_uom_qty
            rec.total_quantity = total_quantity

    @api.depends('order_line_ids.price_subtotal', 'amount_untaxed')
    def _untax_amount(self):
        for rec in self:
            amount_untaxed = 0
            for line in rec.order_line_ids:
                amount_untaxed += line.price_subtotal
            rec.amount_untaxed = amount_untaxed

    @api.depends('order_line_ids.price_subtotal')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line_ids:
                amount_untaxed += line.price_subtotal
            order.update({
                'amount_total': amount_untaxed + amount_tax
            })




    class thong_tin_order_line(models.Model):
        _name = 'order.line'


        order_line_id = fields.Many2one('sale.order.return')
        product_id = fields.Many2one('product.product', string='Sản phẩm')
        invoice_name = fields.Char(string='Tên Hoá Đơn')
        product_uom_qty = fields.Float(string='Ordered Qty', default=1.0)
        check_box_prinizi_confirm = fields.Boolean(default=False, string="Confirm Print")
        print_qty = fields.Float(string='Print Qty', digits=(16, 0))
        price_unit = fields.Float(string='Unit Price', default=0.0)
        price_subtotal = fields.Float(string='Subtotal', compute='_compute_amount', default=0.0)

        @api.onchange('product_uom_qty')
        def onchange_product_uom_qty(self):
            if self.product_uom_qty and self.order_line_id.sale_order_return_ids:
                line_ids = self.order_line_id.sale_order_return_ids.order_line.filtered(lambda line: line.product_id == self.product_id)
                if self.product_uom_qty > sum(line_ids.mapped('product_uom_qty')):
                    raise ValidationError(_("Tổng số lượng sp %s trả lại không thể lớn hơn %s." % (line_ids.product_id.name, sum(line_ids.mapped('product_uom_qty')))))


        @api.depends('price_unit', 'product_uom_qty', 'price_subtotal')
        def _compute_amount(self):
            for rec in self:
                    rec.price_subtotal = rec.price_unit * rec.product_uom_qty

