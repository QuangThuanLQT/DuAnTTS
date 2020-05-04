# -*- coding: utf-8 -*-

from odoo import models, fields, api


class tts_modifier_sale(models.Model):
    _inherit = 'sale.order'

    payment_address = fields.Char('Địa chỉ giao hàng')
    note = fields.Text('Diễn giải')

    date_order = fields.Datetime(string='Order Date', readonly=True, index=True, default=fields.Datetime.now)

    so_tien_da_thu = fields.Float(string='Số tiền đã thu')
    con_phai_thu = fields.Float(string='Số tiền còn phải thu')
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
         ('delivery', 'Giao tới tận nơi'),
         ('transport', 'Giao tới nhà xe'), ], string='Phương thức giao hàng', required=True, default='warehouse',
        states={'sale': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    transport_route_id = fields.Many2one('tuyen.xe', string='Tuyến xe')
    delivery_scope_id = fields.Many2one('pham.vi.giao.hang', string='Phạm vi giao hàng')
    trang_thai_dh = fields.Selection([
        ('wait_pick', 'Chờ Lấy Hàng'), ('ready_pick', 'Sẵn Sàng Lấy Hàng'), ('pick', 'Đang Lấy Hàng'),
        ('wait_pack', 'Chờ Lấy Đóng Gói'), ('pack', 'Đang Đóng Gói'),
        ('wait_out', 'Chờ Xuất Kho'), ('out', 'Đang Giao Hàngy'),
        ('done', 'Done'),
    ], string='Trạng thái đơn hàng')
    create_uid = fields.Many2one('res.users')
    confirm_user_id = fields.Many2one('res.users')

    total_quantity = fields.Float(string='Tổng số lượng', compute='_get_total_quantity')
    delivery_amount = fields.Float(string="Phụ phí giao hàng")
    tong_phi_in = fields.Float(string='Tổng phí in')
    transport_amount = fields.Float(string="Trả trước phí ship nhà xe")

    @api.depends('order_line')
    def _get_total_quantity(self):
        for rec in self:
            total_quantity = 0
            for line in rec.order_line:
                total_quantity += line.product_uom_qty
            rec.total_quantity = total_quantity
