# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import StringIO
import xlsxwriter
import pytz
from datetime import datetime
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class res_partner(models.Model):
    _inherit = 'res.partner'

    def _get_domain_user(self):
        group_nvkd = self.env.ref('tts_modifier_access_right.group_nvkd').users
        group_truong_kd = self.env.ref('tts_modifier_access_right.group_truong_kd').users
        # group_sale_purchase_manager = self.env.ref('tts_modifier_access_right.group_sale_purchase_manager').users
        return [('id', 'in', group_nvkd.ids + group_truong_kd.ids)]

    payment_method = fields.Many2one('account.journal', string="Hình thức thanh toán",
                                     domain=[('type', 'in', ['cash', 'bank'])])
    last_invoice_date = fields.Date('Ngày giao dịch', compute='_compute_last_invoice_date', store=False)
    last_invoice_date_sub = fields.Date('Ngày giao dịch cuối cùng')
    sale_total_amount = fields.Float(compute='_compute_sale_total_amount')
    sale_type = fields.Selection([('allow', 'Cho phép kinh doanh'), ('stop', 'Ngừng kinh doanh')], string='Trạng thái',
                                 default='allow')
    sale_amount = fields.Float(compute='_compute_sale_total_amount')
    return_amount = fields.Float('Tổng trả hàng', compute='_compute_sale_total_amount')
    active = fields.Boolean(default=True, string="Active")
    maKH = fields.Char(string='Mã KH', size=4)
    user_id = fields.Many2one(domain=_get_domain_user)
    loai_hinh_kd_id = fields.Many2one('loai.hinh.kinh.doanh',string='Loại hình kinh doanh')

    # _sql_constraints = [
    #     ('maKH_uniq', 'unique(maKH)', 'Duplicate Customer Code. Please Enter Again !'),
    # ]

    @api.constrains('maKH')
    def _check_ma_KH(self):
        for r in self:
            if r.maKH:
                exists = self.env['res.partner'].search(
                    [('maKH', '=', r.maKH), ('id', '!=', r.id)])
                if exists:
                    raise exceptions.ValidationError("Mã KH Bị Trùng. Xin Vui Lòng Nhập Lại!")

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.model
    def create(self, val):
        if not self._context.get('create_user', False):
            if val.get('customer', False):
                val['ref'] = self.env['ir.sequence'].next_by_code('res.ref.partner')
            if val.get('supplier', False):
                val['ref'] = self.env['ir.sequence'].next_by_code('vendor.sequence')
        res = super(res_partner, self).create(val)
        return res

    @api.onchange('sale_type')
    def _onchange_sale_type(self):
        for rec in self:
            if self.sale_type == 'allow':
                self.active = True
            else:
                self.active = False

    def _compute_sale_total_amount(self):
        for record in self:
            sale_amount = return_amount = 0
            sale_ids = self.env['sale.order'].search(
                [('partner_id', '=', record.id), ('sale_order_return', '=', False)]).filtered(
                lambda s: s.trang_thai_dh == 'done')
            for order in sale_ids:
                sale_amount += order.amount_total
            sale_return_ids = self.env['sale.order'].search(
                [('partner_id', '=', record.id), ('sale_order_return', '=', True)]).filtered(
                lambda s: s.trang_thai_dh == 'done')
            for order_return in sale_return_ids:
                return_amount += order_return.amount_total
            # code for Vendors
            purchase_ids = self.env['purchase.order'].search(
                [('partner_id', '=', record.id), ('purchase_order_return', '=', False)]).filtered(
                lambda s: s.operation_state == 'done')
            for purchase in purchase_ids:
                sale_amount += purchase.amount_total
            purchase_return_ids = self.env['purchase.order'].search(
                [('partner_id', '=', record.id), ('purchase_order_return', '=', True)]).filtered(
                lambda s: s.operation_state == 'done')
            for purchase_return in purchase_return_ids:
                return_amount += purchase_return.amount_total

            record.sale_total_amount = sale_amount - return_amount
            record.sale_amount = sale_amount
            record.return_amount = return_amount

    @api.multi
    def _compute_last_invoice_date(self):
        for record in self:
            order_ids = self.env['sale.order'].search([('partner_id', '=', record.id), ('state', '=', 'sale')],
                                                      order="confirmation_date desc")
            if order_ids:
                last_invoice_date = order_ids[0].confirmation_date
                record.last_invoice_date = last_invoice_date
                self._cr.execute(
                    "UPDATE res_partner SET last_invoice_date_sub = '%s' WHERE id = %s" % (
                    last_invoice_date, record.id))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name:
            args = args if args else []
            args.extend(['|', ['name', 'ilike', name], ['phone', 'ilike', name]])
            name = ''
        res = super(res_partner, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return res

    # Export data
    @api.model
    def print_partner_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        partner_ids = self.env['res.partner'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Customers')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)

        summary_header = ['Code Customer', 'Name Customer', 'Phone', 'Saleperson', 'Create on',
                          'Ngày giao dịch cuối cùng', 'Tổng bán', 'Tổng trả hàng', 'Tổng bán trừ tổng trả hàng',
                          'Trạng thái', 'Sinh nhật', 'PK theo Danh Mục KD', 'PK theo Mô Hình KD']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for partner_id in partner_ids:
            row += 1
            sale_type = dict(self.env['res.partner'].fields_get(allfields=['sale_type'])['sale_type'][
                                 'selection'])
            # user_tz = self.env.user.tz or self._context.get('tz', False) or pytz.utc
            # local = pytz.timezone(user_tz)
            # create_date = datetime.strftime(pytz.utc.localize(datetime.strptime(partner_id.create_date, DT)).astimezone(local), DT)

            create_date = ''
            if partner_id.create_date:
                create_date = self._get_datetime_utc(partner_id.create_date)

            worksheet.write(row, 0, partner_id.ref or '')
            worksheet.write(row, 1, partner_id.name)
            worksheet.write(row, 2, partner_id.phone or '')
            worksheet.write(row, 3, partner_id.user_id.name or '')
            worksheet.write(row, 4, create_date)
            worksheet.write(row, 5, datetime.strptime(partner_id.last_invoice_date, "%Y-%m-%d").strftime(
                "%d/%m/%Y") if partner_id.last_invoice_date else '' or '')
            worksheet.write(row, 6, partner_id.sale_amount, body_bold_color_number)
            worksheet.write(row, 7, partner_id.return_amount, body_bold_color_number)
            worksheet.write(row, 8, partner_id.sale_total_amount, body_bold_color_number)
            worksheet.write(row, 9, sale_type.get(partner_id.sale_type))
            worksheet.write(row, 10, partner_id.feosco_birthday or '')
            worksheet.write(row, 11, partner_id.group_kh1_id.name or '')
            worksheet.write(row, 12, partner_id.group_kh2_id.name or '')
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_vendors_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        partner_ids = self.env['res.partner'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Vendors')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:J', 20)

        summary_header = ['Code Customer', 'Name Vendor', 'Phone', 'Saleperson', 'Create on',
                          'Ngày giao dịch cuối cùng', 'Tổng bán', 'Tổng trả hàng', 'Tổng bán trừ tổng trả hàng',
                          'Trạng thái']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for partner_id in partner_ids:
            row += 1
            sale_type = dict(self.env['res.partner'].fields_get(allfields=['sale_type'])['sale_type'][
                                 'selection'])
            # user_tz = self.env.user.tz or self._context.get('tz', False) or pytz.utc
            # local = pytz.timezone(user_tz)
            # create_date = datetime.strftime(pytz.utc.localize(datetime.strptime(partner_id.create_date, DT)).astimezone(local), DT)

            create_date = ''
            if partner_id.create_date:
                create_date = self._get_datetime_utc(partner_id.create_date)

            worksheet.write(row, 0, partner_id.ref or '')
            worksheet.write(row, 1, partner_id.name)
            worksheet.write(row, 2, partner_id.phone or '')
            worksheet.write(row, 3, partner_id.user_id.name or '')
            worksheet.write(row, 4, create_date)
            worksheet.write(row, 5, datetime.strptime(partner_id.last_invoice_date, "%Y-%m-%d").strftime(
                "%d/%m/%Y") if partner_id.last_invoice_date else '' or '')
            worksheet.write(row, 6, partner_id.sale_amount, body_bold_color_number)
            worksheet.write(row, 7, partner_id.return_amount, body_bold_color_number)
            worksheet.write(row, 8, partner_id.sale_total_amount, body_bold_color_number)
            worksheet.write(row, 9, sale_type.get(partner_id.sale_type))
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_partner_detail_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        partner_ids = self.env['res.partner'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        today = date.today()
        d1 = today.strftime("%d/%m/%Y")
        worksheet = workbook.add_worksheet('Customer Details - %s' % d1)

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:Z', 30)

        summary_header = ['Mã KH', 'Title', 'Tên KH', 'Ngày tạo', 'Điện thoại', 'Di động', 'Địa chỉ', 'Phường/Xã',
                          'Quận/Huyện', 'Tỉnh/Thành phố', 'Salesperson', 'Phương thức giao hàng',
                          'Hình thức thanh toán', 'Ngày giao dịch cuối cùng', 'Tổng bán', 'Tổng trả hàng',
                          'Tổng bán trừ tổng trả hàng', 'Sinh nhật', 'Website', 'Email',
                          'Nhóm KH1', 'Nhóm KH2', 'Trạng thái']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for partner_id in partner_ids:
            row += 1
            sale_type = dict(self.env['res.partner'].fields_get(allfields=['sale_type'])['sale_type'][
                                 'selection'])
            delivery_method = dict(self.env['res.partner'].fields_get(allfields=['delivery_method'])['delivery_method'][
                                       'selection'])
            # user_tz = self.env.user.tz or self._context.get('tz', False) or pytz.utc
            # local = pytz.timezone(user_tz)
            # create_date = datetime.strftime(pytz.utc.localize(datetime.strptime(partner_id.create_date, DT)).astimezone(local), DT)

            create_date = ''
            if partner_id.create_date:
                create_date = self._get_datetime_utc(partner_id.create_date)

            worksheet.write(row, 0, partner_id.ref or '')
            worksheet.write(row, 1, partner_id.title.name or '')
            worksheet.write(row, 2, partner_id.name)
            worksheet.write(row, 3, create_date)
            worksheet.write(row, 4, partner_id.phone or '')
            worksheet.write(row, 5, partner_id.mobile or '')
            worksheet.write(row, 6, partner_id.street or '')
            worksheet.write(row, 7, partner_id.feosco_ward_id.name or '')
            worksheet.write(row, 8, partner_id.feosco_district_id.name or '')
            worksheet.write(row, 9, partner_id.feosco_city_id.name or '')
            worksheet.write(row, 10, partner_id.user_id.name or '')
            worksheet.write(row, 11, delivery_method.get(partner_id.delivery_method))
            worksheet.write(row, 12, partner_id.payment_method.name)
            worksheet.write(row, 13, datetime.strptime(partner_id.last_invoice_date, "%Y-%m-%d").strftime(
                "%d/%m/%Y") if partner_id.last_invoice_date else '' or '')
            worksheet.write(row, 14, partner_id.sale_amount, body_bold_color_number)
            worksheet.write(row, 15, partner_id.return_amount, body_bold_color_number)
            worksheet.write(row, 16, partner_id.sale_total_amount, body_bold_color_number)
            worksheet.write(row, 17, partner_id.feosco_birthday or '')
            worksheet.write(row, 18, partner_id.website or '')
            worksheet.write(row, 19, partner_id.email or '')
            worksheet.write(row, 20, partner_id.group_kh1_id.name or '')
            worksheet.write(row, 21, partner_id.group_kh2_id.name or '')
            worksheet.write(row, 22, sale_type.get(partner_id.sale_type))
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_vendors_detail_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        partner_ids = self.env['res.partner'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        today = date.today()
        d1 = today.strftime("%d/%m/%Y")
        worksheet = workbook.add_worksheet('Customer Details - %s' % d1)

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:Z', 30)

        summary_header = ['Mã KH', 'Title', 'Tên KH', 'Ngày tạo', 'Điện thoại', 'Di động', 'Địa chỉ', 'Phường/Xã',
                          'Quận/Huyện', 'Tỉnh/Thành phố', 'Salesperson', 'Phương thức giao hàng',
                          'Hình thức thanh toán', 'Ngày giao dịch cuối cùng', 'Tổng bán', 'Tổng trả hàng',
                          'Tổng bán trừ tổng trả hàng', 'Sinh nhật', 'Website', 'Email',
                          'Nhóm KH1', 'Nhóm KH2', 'Trạng thái']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for partner_id in partner_ids:
            row += 1
            sale_type = dict(self.env['res.partner'].fields_get(allfields=['sale_type'])['sale_type'][
                                 'selection'])
            delivery_method = dict(self.env['res.partner'].fields_get(allfields=['delivery_method'])['delivery_method'][
                                       'selection'])
            # user_tz = self.env.user.tz or self._context.get('tz', False) or pytz.utc
            # local = pytz.timezone(user_tz)
            # create_date = datetime.strftime(pytz.utc.localize(datetime.strptime(partner_id.create_date, DT)).astimezone(local), DT)

            create_date = ''
            if partner_id.create_date:
                create_date = self._get_datetime_utc(partner_id.create_date)

            worksheet.write(row, 0, partner_id.ref or '')
            worksheet.write(row, 1, partner_id.title.name or '')
            worksheet.write(row, 2, partner_id.name)
            worksheet.write(row, 3, create_date)
            worksheet.write(row, 4, partner_id.phone or '')
            worksheet.write(row, 5, partner_id.mobile or '')
            worksheet.write(row, 6, partner_id.street or '')
            worksheet.write(row, 7, partner_id.feosco_ward_id.name or '')
            worksheet.write(row, 8, partner_id.feosco_district_id.name or '')
            worksheet.write(row, 9, partner_id.feosco_city_id.name or '')
            worksheet.write(row, 10, partner_id.user_id.name or '')
            worksheet.write(row, 11, delivery_method.get(partner_id.delivery_method))
            worksheet.write(row, 12, partner_id.payment_method.name)
            worksheet.write(row, 13, datetime.strptime(partner_id.last_invoice_date, "%Y-%m-%d").strftime(
                "%d/%m/%Y") if partner_id.last_invoice_date else '' or '')
            worksheet.write(row, 14, partner_id.sale_amount, body_bold_color_number)
            worksheet.write(row, 15, partner_id.return_amount, body_bold_color_number)
            worksheet.write(row, 16, partner_id.sale_total_amount, body_bold_color_number)
            worksheet.write(row, 17, partner_id.feosco_birthday or '')
            worksheet.write(row, 18, partner_id.website or '')
            worksheet.write(row, 19, partner_id.email or '')
            worksheet.write(row, 20, partner_id.group_kh1_id.name or '')
            worksheet.write(row, 21, partner_id.group_kh2_id.name or '')
            worksheet.write(row, 22, sale_type.get(partner_id.sale_type))
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


class res_partner_ihr(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, val):
        res = super(res_partner_ihr, self.with_context(create_user=True)).create(val)
        res.partner_id.email = res.login
        return res
