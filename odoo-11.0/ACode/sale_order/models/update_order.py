# -*- coding: utf-8 -*-

from odoo import models, fields, api


class dat_coc(models.Model):
    _inherit = 'res.partner'

    dat_coc = fields.Float('Đặt cọc', digits=(16, 2))
    sale_amount = fields.Float('Tổng bán')
    return_amount = fields.Float('Tổng trả hàng')
    sale_total_amount = fields.Float('Tổng bán trừ tổng trả hàng')


class tts_modifier_sale(models.Model):
    _inherit = 'sale.order'

    payment_address = fields.Char('Địa chỉ giao hàng', required=0)
    notes = fields.Text('Diễn giải')

    date_order = fields.Datetime(string='Order Date', readonly=True, index=True, default=fields.Datetime.now)
    tien_coc = fields.Float(string='KH đặt cọc', related='partner_id.dat_coc', digits=(16, 2))
    so_tien_da_thu = fields.Float(string='Số tiền đã thu', digits=(16, 2))
    con_phai_thu = fields.Float(string='Số tiền còn phải thu', compute='_con_phai_thu')
    trang_thai_tt = fields.Selection(
        [('chua_tt', 'Chưa thanh toán'),
         ('tt_1_phan', 'Thanh toán 1 phần'),
         ('done_tt', 'Hoàn tất thanh toán')],
        string='Trạng thái thanh toán', default='chua_tt')
    payment_method = fields.Many2one('account.journal', string="Hình thức thanh toán",
                                     domain=[('type', 'in', ['cash', 'bank'])], required=0)
    quy_trinh_ban_hang = fields.Selection([('print', 'Có In'), ('noprint', 'Không In')], string='Quy trình bán hàng',
                                          default='noprint')
    delivery_method = fields.Selection(
        [('warehouse', 'Tới kho lấy hàng'),
         ('delivery', 'Giao tới tận nơi')], string='Phương thức giao hàng', required=True, default='warehouse',
        states={'sale': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    # transport_route_id = fields.Many2one('tuyen.xe', string='Tuyến xe')
    # delivery_scope_id = fields.Many2one('pham.vi.giao.hang', string='Phạm vi giao hàng')
    # transport_amount = fields.Float(string="Trả trước phí ship nhà xe", readonly=True)
    trang_thai_dh = fields.Selection([
        ('wait_pick', 'Chờ Lấy Hàng'), ('ready_pick', 'Sẵn Sàng Lấy Hàng'), ('pick', 'Đang Lấy Hàng'),
        ('wait_pack', 'Chờ Lấy Đóng Gói'), ('pack', 'Đang Đóng Gói'),
        ('wait_out', 'Chờ Xuất Kho'), ('out', 'Đang Giao Hàngy'),
        ('done', 'Done'),
    ], string='Trạng thái đơn hàng')
    create_uid = fields.Many2one('res.users')
    confirm_user_id = fields.Many2one('res.users')

    total_quantity = fields.Float(string='Tổng số lượng', compute='_get_total_quantity')
    delivery_amount = fields.Float(string="Chi phí giao hàng", compute='get_delivery_amount', store=True)
    tong_phi_in = fields.Float(string='Tổng phí in')

    # .......tính phí giao hàng theo tổng đơn hàng..
    @api.depends('delivery_method', 'order_line.price_total')
    def get_delivery_amount(self):
        for rec in self:
            if rec.delivery_method == 'delivery' and rec.amount_untaxed > 20000000:
                rec.delivery_amount = 0
            elif rec.delivery_method == 'delivery' and rec.amount_untaxed < 5000000:
                rec.delivery_amount = 30000
            elif rec.delivery_method == 'warehouse':
                rec.delivery_amount = 0
            else:
                rec.delivery_amount = 50000

    @api.onchange('so_tien_da_thu')
    def auto_money(self):
        self.tien_coc -= self.so_tien_da_thu
        data = []
        record_ids = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
        for record in record_ids:
            record.dat_coc = self.tien_coc
            record.write({
                'dat_coc': self.tien_coc
            })

    # update tong tien có chi phi gia hang
    @api.depends('order_line.price_total', 'delivery_amount', 'tong_phi_in')
    def _amount_all(self):
        res = super(tts_modifier_sale, self)._amount_all()
        for order in self:
            order.update({
                'amount_total': order.amount_untaxed + order.amount_tax + order.delivery_amount + order.tong_phi_in,
            })

    # tien can thu
    @api.depends('amount_total', 'so_tien_da_thu')
    def _con_phai_thu(self):
        for rec in self:
            rec.con_phai_thu = rec.amount_total - rec.so_tien_da_thu

    @api.depends('order_line')
    def _get_total_quantity(self):
        for rec in self:
            total_quantity = 0
            for line in rec.order_line:
                total_quantity += line.product_uom_qty
            rec.total_quantity = total_quantity

    tax_id = fields.Many2one('account.tax', string='Thuế')
    discount_type = fields.Selection([('percent', 'Tỷ lên phần trăm'), ('amount', 'Số tiền')],
                                     string='Loại giảm giá', default='percent')
    discount_rate = fields.Float('Tỷ lệ chiết khấu')
    check_box_co_cq = fields.Boolean(default=False, string="CO, CQ")
    check_box_invoice_gtgt = fields.Boolean(default=False, string="Invoice GTGT")

    @api.onchange('delivery_method', 'partner_id')
    def onchange_delivery_method(self):
        if self.delivery_method == 'delivery':
            self.payment_address = "%s, %s, %s, %s" % (
                self.partner_id.zip or '', self.partner_id.city.name or '',
                self.partner_id.street2.name or '',
                self.partner_id.street.name or '')

    # hình thức giao tới tận nơi: tổng các mặt hàng
    # trên 20 triệu đồng miễn phí vận chuyển
    # từ 5 triệu đồng - < 20 triệu đồng chịu 50.000 phí vận chuyển
    # còn lại đơn dưới 5 triệu đồng sẽ chịu 30.000 phí vận chuyển

    @api.multi
    def print_excel(self):
        return self.env.ref('sale_order_return.action_report_excel_nhap_kho').report_action(self)