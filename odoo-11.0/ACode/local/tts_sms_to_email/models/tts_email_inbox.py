# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import StringIO
import xlsxwriter
import pytz
import re
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class tts_sms_inbox(models.Model):
    _name = 'tts.sms.inbox'
    _order = 'date desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'utm.mixin', 'rating.mixin']

    name = fields.Char()
    subject = fields.Char()
    phone = fields.Char('Bank')
    body = fields.Text(string='SMS Text', store=True, track_visibility='onchange')
    date = fields.Datetime('Date', track_visibility='onchange')
    amount = fields.Float('Số tiền', track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', string='Khách hàng', track_visibility='onchange')
    customer_name = fields.Char(string='Khách hàng', compute='_get_customer_name', store=True)
    customer_phone = fields.Char('Điện thoại', )
    user_id = fields.Many2one('res.users', string='Salesperson')
    state = fields.Selection([
        ('draft', 'Chưa tạo phiếu'),
        ('done', 'Đã tạo phiếu')], 'Status', default='draft', readonly=True)
    ma_kh = fields.Char()
    don_hang = fields.Char('Đơn hàng')
    add_check = fields.Boolean(compute='get_check_add', store=True)
    account_voucher_id = fields.Many2one('account.voucher', string='Chi tiết', readonly=True, copy=False,
                                         track_visibility='onchange')
    create_uid_voucher = fields.Many2one('res.users', string='Người tạo phiếu thu', readonly=True,
                                         track_visibility='onchange')
    create_date_voucher = fields.Datetime(string='Thời gian tạo phiếu thu', readonly=True, track_visibility='onchange')
    account_voucher_line = fields.One2many('account.voucher', 'sms_payment_id')
    created_voucher = fields.Boolean()
    infor_customer = fields.Selection([
        ('yes', 'Có mã KH'),
        ('no', 'Không có mã KH')], 'TT mã KH', readonly=True, compute=False, store=True)
    city_id = fields.Many2one('feosco.city', string="Tỉnh")

    _sql_constraints = [
        ('ma_kh_unique', 'check(1=1)', 'No error'),
    ]

    @api.depends('ma_kh')
    def get_infor_ref_customer(self):
        for record in self:
            if record.ma_kh:
                record.infor_customer = 'yes'
            else:
                record.infor_customer = 'no'

    @api.depends('body')
    def get_check_add(self):
        for record in self:
            if '+' in record.body:
                record.add_check = True

    @api.depends('customer_id')
    def _get_customer_name(self):
        for record in self:
            if record.customer_id:
                record.customer_name = record.customer_id.name

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('sms.assemble') or 'New'
        # vals['ma_kh'] = self.env['ir.sequence'].next_by_code('ma_kh.assemble') or 'New'
        if 'body' in vals:
            data = self._get_customer_data(vals['body'])
            vals.update({k: v for k, v in data.items() if v != False and v != ''})
        res = super(tts_sms_inbox, self).create(vals)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(tts_sms_inbox, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                    orderby=orderby,
                                                    lazy=lazy)
        return res

    @api.multi
    def write(self, val):
        res = super(tts_sms_inbox, self).write(val)
        if 'not_write' not in self._context:
            data = self._get_customer_data(self.body)
            vals = {k: v for k, v in data.items() if v != False and v != ''}
            if vals:
                self.with_context(not_write=True).write(vals)
        return res

    def create_account_voucher(self):
        view_id = self.env.ref('account_voucher.view_sale_receipt_form')
        payment_medthod_id = self.env['account.journal'].search([('type', '=', 'bank'), ('bank_name', '=', self.phone)],
                                                                limit=1)
        action = {
            'name': 'Sales Receipts',
            'type': 'ir.actions.act_window',
            'res_model': 'account.voucher',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'target': 'new',
            'context': {
                'default_voucher_type': 'sale',
                'voucher_type': 'sale',
                'default_payment_journal_id': payment_medthod_id.id,
                'payment_journal_id': payment_medthod_id.id,
                'default_partner_id': self.customer_id.id,
                'partner_id': self.customer_id.id,
                'default_amount_input': self.amount,
                'amount_input': self.amount,
                'default_sms_payment_id': self.id,
            }
        }
        return action

    def view_account_voucher(self):
        view_id = self.env.ref('account_voucher.view_sale_receipt_form')
        action = {
            'name': 'Sales Receipts',
            'type': 'ir.actions.act_window',
            'res_model': 'account.voucher',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.account_voucher_id.id,
            'view_id': view_id.id,
            'target': 'current',
        }
        return action

    @api.model
    def message_new(self, msg, custom_values=None):
        values = dict(custom_values or {}, subject=msg.get('subject'))
        format = re.compile('<.*?>')
        message = re.sub(format, '', msg.get('body', False))
        data = self.get_data_from_message(message)
        if len(data) >= 3:
            subject = data[0].strip()
            phone = data[1].strip()
            body = data[2].strip()
            date = msg.get('date')
            # customer_data = self._get_customer_data(body)
            values.update({
                'date': date if date else False,
                'phone': phone,
                'body': body,
                'subject': subject
                # 'customer_id': customer_data.get('customer_id', False),
                # 'customer_phone': customer_data.get('customer_phone', ''),
                # 'user_id': customer_data.get('user_id', False),
                # 'amount': customer_data.get('amount', ''),
                # 'ma_kh': customer_data.get('ma_kh', ''),
                # 'don_hang': customer_data.get('don_hang', ''),
            })
            sms_id = False
            if body[:3] in ['(1)', '(0)']:
                sms_id = self.search([('phone', '=', phone), ('date', '=', date)], limit=1)
                if not sms_id:
                    domain = [('phone', '=', phone)]
                    date_start = (
                        datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(seconds=1)).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT)
                    date_end = (
                        datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(seconds=1)).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT)
                    domain.append(('subject', '=', subject))
                    domain.append(('date', '<=', date_end))
                    domain.append(('date', '>=', date_start))

                    sms_id = self.search(domain, limit=1)

            else:
                date_end = date
                date_start = (datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(seconds=5)).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
                sms_ids = self.search([('phone', '=', phone), ('date', '>=', date_start), ('date', '<=', date_end)],
                                      order='date desc')
                if sms_ids:
                    sms_id = sms_ids[0]
            if sms_id:
                if body[0:3] == '(0)':
                    body_html = body[3:]
                    body_sms = sms_id.body[3:] + body_html
                elif body[0:3] == '(1)':
                    body_sms = body[3:] + sms_id.body[3:] if len(sms_id.body) > 3 else ''
                else:
                    body_sms = sms_id.body + body

                # data_write = {k: v for k, v in values.items() if v != False and v != ''}
                # data_write['body'] = body_sms
                data_write = {'body': body_sms}

                sms_id.write(data_write)
                return sms_id.id
        res = super(tts_sms_inbox, self).message_new(msg, custom_values=values)
        return res

    def _get_customer_data(self, body):
        data = {}
        customer_phone = ''
        customer_id = False
        ma_kh = ''
        number_kh = False
        don_hang = ''
        user_id = False
        city_id = False
        for value in body.split():
            if "KH" in value.upper():
                for i in range(0, len(value.upper())):
                    if value[i].upper() == 'K' and (i + 1) < len(value.upper()) and value[i + 1].upper() == 'H':
                        num = value[i + 2:i + 6]
                        if len(num.replace(' ', '')) == 4 and num.isdigit() == True:
                            number_kh = num
                            ma_kh = "KH" + num

                            # index = value.upper().index('KH') + 1
                            # num = value.upper()[index+1:index + 5]
                            # if len(num.replace(' ', '')) == 4 and num.isdigit() == True:
                            #     number_kh = num
                            #     ma_kh = "KH" + num
            if "SO0" in value.upper() and len(value) >= 13:
                index = value.upper().index('S')
                so_number = value.upper()[index:index + 13]
                don_hang = so_number
        if not number_kh:
            # for value in body.split():
            #     if value.upper() == 'KH':
            #         index = body.split().index(value) + 1
            #         num = body.split()[index]
            #         if index < len(body.split()) and len(num) == 4 and num.isdigit() == True:
            #             ma_kh = "KH" + num
            #             number_kh = num
            for i in range(0, len(body)):
                if body[i].upper() == 'K' and (i + 1) < len(body.upper()) and body[i + 1].upper() == 'H' \
                        and (i + 2) < len(body.upper()) and body[i + 2] == ' ':
                    char_num = ''
                    for k in range(i + 2, len(body)):
                        if body[k].isdigit() == True:
                            char_num += body[k]
                            if len(char_num) == 4:
                                break
                    if len(char_num) == 4:
                        number_kh = char_num
                        ma_kh = "KH" + char_num
            
        if ma_kh:
            customer = self.env['res.partner'].search([('maKH', '=', number_kh)])
            if customer:
                customer_id = customer.id
                customer_phone = customer.phone
                user_id = customer.user_id.id
                city_id = customer.feosco_city_id.id
        amount_string = ''
        index = body.find('+')
        if index != -1:
            character = list(body)
            for i in range(index + 1, len(character)):
                if character[i] in ['', ',', '.']:
                    pass
                if character[i].isdecimal() == True:
                    amount_string += character[i]
                if character[i].isalpha() == True:
                    break
                if character[i] in ['('] == True:
                    break
        try:
            amount = float(amount_string)
        except:
            amount = 0
        return {
            'customer_phone': customer_phone,
            'customer_id': customer_id,
            'amount': amount,
            'ma_kh': ma_kh,
            'don_hang': don_hang,
            'user_id': user_id,
            'city_id': city_id,
            'infor_customer': 'yes' if customer_id else 'no'
        }

    def get_data_from_message(self, message):
        data = []
        temp = 0
        string = ''
        index = 0
        listmess = list(message)
        for i in range(0, len(listmess)):
            if listmess[i] != ',':
                string += listmess[i]
            else:
                temp += 1
                data.append(string)
                string = ''
                if temp == 2:
                    sms_text = message[i + 1:]
                    data.append(sms_text)
                    break
        return data

    ## Todo print report excel

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.model
    def print_sms_detail(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        partner_ids = self.env['tts.sms.inbox'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Customers')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)
        worksheet.set_column('C:C', 60)

        summary_header = ['Thời gian nhận', 'Ngân hàng', 'Nội dung tin nhắn', 'Số tiền', 'Đơn hàng', 'Mã KH',
                          'Khách hàng', 'Điện thoại', 'Salesperson', 'Người tạo phiếu thu',
                          'Thời gian tạo phiếu thu', 'Chi tiết', 'Trạng thái', 'TT mã KH', 'Tỉnh']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for partner_id in partner_ids:
            row += 1
            state = dict(self.env['tts.sms.inbox'].fields_get(allfields=['state'])['state'][
                             'selection'])
            infor_customer = dict(self.env['tts.sms.inbox'].fields_get(allfields=['infor_customer'])['infor_customer'][
                                      'selection'])

            create_date = self._get_datetime_utc(partner_id.date)
            create_date_voucher = self._get_datetime_utc(
                partner_id.create_date_voucher) if partner_id.create_date_voucher else ''
            worksheet.write(row, 0, create_date or '', text_style)
            worksheet.write(row, 1, partner_id.phone, text_style)
            worksheet.write(row, 2, partner_id.body or '', text_style)
            worksheet.write(row, 3, partner_id.amount or '', body_bold_color_number)
            worksheet.write(row, 4, partner_id.don_hang or '', text_style)
            worksheet.write(row, 5, partner_id.ma_kh or '', text_style)
            worksheet.write(row, 6, partner_id.customer_id.name or '', text_style)
            worksheet.write(row, 7, partner_id.customer_phone or '', text_style)
            worksheet.write(row, 8, partner_id.user_id.name or '', text_style)
            worksheet.write(row, 9, partner_id.create_uid_voucher.name or '', text_style)
            worksheet.write(row, 10, create_date_voucher, text_style)
            worksheet.write(row, 11, partner_id.account_voucher_id.name or '', text_style)
            worksheet.write(row, 12, state.get(partner_id.state), text_style)
            worksheet.write(row, 13, infor_customer.get(partner_id.infor_customer), text_style)
            worksheet.write(row, 14, partner_id.city_id.name or '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
