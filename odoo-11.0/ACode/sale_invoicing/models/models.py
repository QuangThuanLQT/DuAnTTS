# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Customer_Invoices(models.Model):
    _inherit = 'account.invoice'

    invoice_date_real = fields.Date(string='Invoice Date Real')
    invoice_number_real = fields.Char(string='Invoice Number Real')
    invoice_total_real = fields.Float(string='Giá Trị Hoá Đơn Thực')
    number_origin = fields.Char(string='Number Origin')


class Customer_Credit_Notes(models.Model):
    _inherit = 'account.invoice'


class Sales_Receipts(models.Model):
    _inherit = 'account.voucher'

    amount_input = fields.Float('Số tiền')
    note = fields.Char(string='Ghi chú')

    journal_id = fcollect_type = fields.Selection([('journal', 'Customer Invoices (VNĐ)')], string='Journal',
                                                  default='journal')

    payment_journal_id = fields.Many2one('account.journal', string='Payment Method')
    account_id = fields.Many2one('account.account', string='Account')

    number_voucher = fields.Char(string='Số phiếu thu')
    name = fields.Char(string='Payment Reference')
    collect_type = fields.Selection([('sale', 'Collect Sale')], string='Collect Type', default='sale')
    payment_date = fields.Datetime(string='Payment Date', readonly=1)
    created_person = fields.Many2one('res.users', string='Created Person', readonly=1)
    check_date = fields.Datetime(string='Check Date', readonly=1)
    checked_person = fields.Many2one('res.users', string='Checked Person', readonly=1)
    validate_date = fields.Datetime(string='Validate Date', readonly=1)
    validated_person = fields.Many2one('res.users', string='Validated Person', readonly=1)

    voucher_sale_line_ids = fields.One2many('voucher.sale.line', 'account_voucher_id', 'Sale order', readonly=True)

    sale_id = fields.Char(string='Sale Order', compute='_compute_total_sale')
    amount_sale = fields.Monetary(string='Total', store=False, readonly=False, compute='_compute_total_sale')
    amount_dathu = fields.Monetary(string='Số tiền đã thu', store=False, readonly=True, compute='_compute_total_sale')
    amount_con_phaithu = fields.Monetary(string='Số tiền còn phải thu', store=False, readonly=True,
                                         compute='_compute_total_sale')


class voucher_sale_line(models.Model):
    _name = 'voucher.sale.line'

    order_id = fields.Many2one('sale.order', string='Đơn hàng')
    order_name = fields.Char(string='Mã SO', related='order_id.name')
    date_order = fields.Datetime(string='Ngày SO', related='order_id.date_order')
    amount_total = fields.Float(string='Tổng tiền')
    so_tien_da_thu = fields.Float(string='Số tiền đã thu', compute=False, store=True)
    con_phai_thu = fields.Float(string='Số tiền còn phải thu', compute=False)
    trang_thai_tt = fields.Selection(
        [('chua_tt', 'Chưa thanh toán'), ('tt_1_phan', 'Thanh toán 1 phần'), ('done_tt', 'Hoàn tất thanh toán')],
        string='Trạng thái thanh toán', compute=False, store=True)
    check = fields.Boolean(string='Chọn')
    account_voucher_id = fields.Many2one('account.voucher')

    @api.depends('order_id.so_tien_da_thu', 'amount_total')
    def _get_line_data(self):
        for rec in self:
            rec.so_tien_da_thu = rec.order_id.so_tien_da_thu
            rec.con_phai_thu = rec.amount_total - rec.order_id.so_tien_da_thu
            rec.trang_thai_tt = rec.order_id.trang_thai_tt


class Payments(models.Model):
    _inherit = 'account.payment'


class Sellable_Products(models.Model):
    _inherit = 'product.product'
