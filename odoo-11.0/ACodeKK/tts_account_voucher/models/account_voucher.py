# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import StringIO
import xlsxwriter
import pytz
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class account_voucher_ihr(models.Model):
    _inherit = 'account.voucher'

    amount_input = fields.Float('Số tiền', readonly=True, states={'draft': [('readonly', False)]})
    voucher_sale_line_ids = fields.One2many('voucher.sale.line', 'account_voucher_id', 'Sale order', readonly=True,
                                            states={'draft': [('readonly', False)]}, )
    payment_date = fields.Datetime(string='Payment Date', readonly=1)
    created_person = fields.Many2one('res.users', string='Created Person', readonly=1)
    check_date = fields.Datetime(string='Check Date', readonly=1)
    checked_person = fields.Many2one('res.users', string='Checked Person', readonly=1)
    validate_date = fields.Datetime(string='Validate Date', readonly=1)
    validated_person = fields.Many2one('res.users', string='Validated Person', readonly=1)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('proforma', 'Pro-forma'),
        ('checked', 'Checked'),
        ('posted', 'Posted')])
    note = fields.Char(string='Ghi Chú')
    sale_id = fields.Char(string='Sale Order', compute='_compute_total_sale')
    amount_sale = fields.Monetary(string='Total', store=False, readonly=False, compute='_compute_total_sale')
    amount_dathu = fields.Monetary(string='Số tiền đã thu', store=False, readonly=True, compute='_compute_total_sale')
    amount_con_phaithu = fields.Monetary(string='Số tiền còn phải thu', store=False, readonly=True,
                                         compute='_compute_total_sale')

    @api.multi
    @api.depends('voucher_sale_line_ids.amount_total', 'voucher_sale_line_ids.check')
    def _compute_total_sale(self):
        for voucher in self:
            total = so_tien_da_thu = con_phai_thu = 0
            for line in voucher.voucher_sale_line_ids:
                if line.check == True:
                    voucher.sale_id = line.order_id.name
                    total += line.amount_total
                    so_tien_da_thu += line.so_tien_da_thu
                    con_phai_thu += line.con_phai_thu
            voucher.amount_sale = total
            voucher.amount_dathu = so_tien_da_thu
            voucher.amount_con_phaithu = con_phai_thu

    @api.multi
    def cancel_voucher(self):
        for rec in self:
            if rec.state in ['checker', 'posted']:
                line_so_id = self.env['voucher.sale.line'].search(
                    [('check', '=', True), ('account_voucher_id', '=', rec.id)], limit=1)
                so_id = line_so_id.order_id
                if not self._context.get('cancel_sale') and so_id:
                    so_tien_da_thu = so_id.so_tien_da_thu - rec.amount_input
                    if so_tien_da_thu <= 0:
                        so_id.write({
                            'so_tien_da_thu': 0,
                            'trang_thai_tt': 'chua_tt'
                        })
                    elif so_tien_da_thu < so_id.amount_total:
                        so_id.write({
                            'so_tien_da_thu': so_tien_da_thu,
                            'trang_thai_tt': 'tt_1_phan'
                        })
            res = super(account_voucher_ihr, self).cancel_voucher()
        return res

    @api.depends('company_id', 'pay_now', 'account_id')
    def _compute_payment_journal_id(self):
        for voucher in self:
            if voucher.pay_now != 'pay_now':
                continue
            domain = [
                ('type', 'in', ('bank', 'cash')),
                ('company_id', '=', voucher.company_id.id),
            ]
            if voucher.account_id and voucher.account_id.internal_type == 'liquidity':
                field = 'default_debit_account_id' if voucher.voucher_type == 'sale' else 'default_credit_account_id'
                domain.append((field, '=', voucher.account_id.id))
            voucher.payment_journal_id = self.env['account.journal'].search(domain, limit=1)
            voucher.account_id = voucher.payment_journal_id.default_debit_account_id

    @api.model
    def create(self, val):
        res = super(account_voucher_ihr, self).create(val)
        res.payment_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        res.created_person = self._uid
        return res

    @api.multi
    def action_checked(self):
        for rec in self:
            line_ids = rec.voucher_sale_line_ids.filtered(lambda l: l.check)
            if line_ids:
                if len(line_ids) > 1:
                    raise ValidationError('Chỉ được chọn một đơn hàng!')
                order_id = line_ids.order_id
                if order_id.state != 'cancel':
                    if order_id.trang_thai_tt == 'done_tt':
                        raise ValidationError('Đơn hàng đã thanh toán!')
                    if order_id.con_phai_thu == rec.amount_input:
                        order_id.trang_thai_tt = 'done_tt'
                        order_id.so_tien_da_thu = order_id.so_tien_da_thu + rec.amount_input
                        order_id.con_phai_thu = order_id.con_phai_thu - rec.amount_input

                        line_ids.so_tien_da_thu = order_id.so_tien_da_thu
                        line_ids.con_phai_thu = line_ids.amount_total - order_id.so_tien_da_thu
                        line_ids.trang_thai_tt = 'done_tt'
                    elif rec.amount_input != 0 and order_id.con_phai_thu > rec.amount_input:
                        order_id.trang_thai_tt = 'tt_1_phan'
                        order_id.so_tien_da_thu = order_id.so_tien_da_thu + rec.amount_input
                        order_id.con_phai_thu = order_id.con_phai_thu - rec.amount_input

                        line_ids.trang_thai_tt = 'tt_1_phan'
                        line_ids.so_tien_da_thu = order_id.so_tien_da_thu
                        line_ids.con_phai_thu = line_ids.amount_total - order_id.so_tien_da_thu
                    else:
                        raise ValidationError('Số tiền của phiếu thu > số tiền còn phải thu')
            else:
                raise ValidationError('Chọn một đơn hàng để thực hiện!')
            order_id = line_ids.order_id
            if order_id.state == 'cancel':
                rec.cancel_voucher()
                action = self.env.ref('tts_account_voucher.show_warning_vourcher_action').read()[0]
                action['context'] = {'default_name': 'Đơn hàng đã hủy trước đó!'}
                return action
            else:
                rec.state = 'checked'
                rec.check_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                rec.checked_person = self._uid

    @api.onchange('partner_id')
    def onchange_partner_add_so(self):
        if self.partner_id:
            order_ids = self.env['sale.order'].search(
                [('sale_order_return', '=', False), ('partner_id', '=', self.partner_id.id),
                 ('trang_thai_tt', '!=', 'done_tt'), ('con_phai_thu', '!=', 0), ('reason_cancel', '=', False)])
            self.voucher_sale_line_ids = None
            line_order_data = self.env['voucher.sale.line']
            for order_id in order_ids:
                line_order = self.voucher_sale_line_ids.new({
                    'order_id': order_id.id,
                    'amount_total': self._get_amount_order(order_id),
                })
                line_order._get_line_data()
                line_order_data += line_order
            if line_order_data:
                self.voucher_sale_line_ids = line_order_data

    @api.multi
    def proforma_voucher(self):
        super(account_voucher_ihr, self).proforma_voucher()
        for rec in self:
            rec.validate_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            rec.validated_person = self._uid

    def _get_amount_order(self, order):
        amount_total = 0
        sql = """SELECT amount_total FROM sale_order WHERE id = %s""" % order.id
        self.env.cr.execute(sql)
        value = self.env.cr.fetchall()
        if value and value[0]:
            amount_total = value[0][0]
        return amount_total

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M:%S')
        return resuft

    @api.model
    def export_sales_receipts_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        voucher_ids = self.env['account.voucher'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sales Receipts')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 14)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 16)
        worksheet.set_column('H:H', 10)
        worksheet.set_column('I:I', 16)
        worksheet.set_column('J:O', 18)
        worksheet.set_column('P:P', 30)

        summary_header = ['Create Date', 'Số Phiếu Thu', 'Sale Order', 'Mã KH', 'Customer', 'Phương thức thanh toán',
                          'Số tiền đã thu', 'Số tiền còn phải thu', 'Total', 'Trang thái phiếu thu',
                          'Payment Date', 'Created Person', 'Check Date', 'Checked Person', 'Validate Date',
                          'Valiadated Person', 'Ghi chú',
                          ]
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for rec in voucher_ids:
            row += 1
            date_payment = ''
            date_check = ''
            date_validate = ''
            if rec.payment_date:
                date_payment = self._get_datetime_utc(rec.payment_date)
            if rec.check_date:
                date_check = self._get_datetime_utc(rec.check_date)
            if rec.validate_date:
                date_validate = self._get_datetime_utc(rec.validate_date)
            worksheet.write(row, 0, rec.create_date)
            worksheet.write(row, 1, rec.number_voucher or '')
            worksheet.write(row, 2, rec.sale_id or '')
            worksheet.write(row, 3, rec.partner_id.ref or '')
            worksheet.write(row, 4, rec.partner_id.name or '')
            worksheet.write(row, 5, rec.payment_journal_id.display_name or '')
            worksheet.write(row, 6, rec.amount_dathu or '')
            worksheet.write(row, 7, rec.amount_con_phaithu or '0.0')
            worksheet.write(row, 8, rec.amount_sale or '')
            worksheet.write(row, 9, rec.state or '')
            worksheet.write(row, 10, date_payment, text_style or '')
            worksheet.write(row, 11, rec.created_person.name or '')
            worksheet.write(row, 12, date_check or '')
            worksheet.write(row, 13, rec.checked_person.name or '')
            worksheet.write(row, 14, date_validate or '')
            worksheet.write(row, 15, rec.validated_person.name or '')
            worksheet.write(row, 16, rec.note or '')
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


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


class show_warning_vourcher(models.TransientModel):
    _name = "show.warning.vourcher"

    name = fields.Char(readonly=1)
