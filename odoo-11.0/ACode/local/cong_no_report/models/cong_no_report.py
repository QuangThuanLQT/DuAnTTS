# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re
import base64
import StringIO
import xlsxwriter
import math
from odoo.tools.misc import formatLang
from odoo.tools.float_utils import float_compare

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class sale_order_no_invoice(models.TransientModel):
    _name = "sale.order.no.invoice"

    no_invoice_order_line_ids = fields.One2many('sale.order.no.invoice.line', 'noinvoice_order_id')
    invalid_order_line_ids = fields.One2many('sale.order.no.invoice.line', 'invalid_order_id')

    @api.model
    def default_get(self, fields):
        res = super(sale_order_no_invoice, self).default_get(fields)

        # Sale order
        line_data = [(6, 0, [])]
        if 'no_invoice_order_ids' in self._context:
            for order_id in self._context.get('no_invoice_order_ids'):
                line_data.append((0, 0, {'sale_order_id': order_id}))
            res['no_invoice_order_line_ids'] = line_data

        line_data = [(6, 0, [])]
        if 'invalid_order_line_ids' in self._context:
            for order_id in self._context.get('invalid_order_line_ids'):
                line_data.append((0, 0, {'sale_order_id': order_id}))
            res['invalid_order_line_ids'] = line_data

        # Purchase order
        line_data = [(6, 0, [])]
        if 'no_invoice_purchase_order_ids' in self._context:
            for order_id in self._context.get('no_invoice_purchase_order_ids'):
                line_data.append((0, 0, {'purchase_order_id': order_id}))
            res['no_invoice_order_line_ids'] = line_data

        line_data = [(6, 0, [])]
        if 'invalid_purchase_order_line_ids' in self._context:
            for order_id in self._context.get('invalid_purchase_order_line_ids'):
                line_data.append((0, 0, {'purchase_order_id': order_id}))
            res['invalid_order_line_ids'] = line_data

        return res

    @api.multi
    def upate_invoice_for_so(self):
        no_invoice_sale_orders = self.no_invoice_order_line_ids.mapped('sale_order_id')
        invalid_sale_orders = self.invalid_order_line_ids.mapped('sale_order_id')

        if invalid_sale_orders:
            invalid_sale_orders.with_context({'active_id': invalid_sale_orders.ids[0], 'active_ids': invalid_sale_orders.ids, }).multi_update_account_invoice()

        for order in no_invoice_sale_orders:
            try:
                order.with_context({'active_id': order.id, 'active_ids': [order.id], }).directly_create_inv()
            except Exception as e:
                raise UserError(_("Can not create invoice for sale order %s!" % (order.name)))

    @api.multi
    def upate_invoice_for_po(self):
        no_invoice_purchase_orders = self.no_invoice_order_line_ids.mapped('purchase_order_id')
        invalid_pruchase_orders = self.invalid_order_line_ids.mapped('purchase_order_id')

        if invalid_pruchase_orders:
            invalid_pruchase_orders.with_context({'active_id': invalid_pruchase_orders.ids[0],
                                              'active_ids': invalid_pruchase_orders.ids, }).multi_update_account_invoice()

        for order in no_invoice_purchase_orders:
            try:
                order.with_context({'active_id': order.id, 'active_ids': [order.id], }).create_invoice_show_view()
            except Exception as e:
                raise UserError(_("Can not create invoice for purchase order %s!" % (order.name)))


class sale_order_no_invoice_line(models.TransientModel):
    _name = "sale.order.no.invoice.line"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    noinvoice_order_id = fields.Many2one('sale.order.no.invoice')
    invalid_order_id = fields.Many2one('sale.order.no.invoice')


class cong_no_report(models.TransientModel):
    _name = 'cong.no.report'

    @api.multi
    def get_account_default(self):
        account_id = self.env['account.account'].search([('code', '=', '131')], limit=1)
        return account_id.id

    partner_id = fields.Many2one('res.partner',string="Customer")
    partner_ids = fields.Many2many('res.partner', string="Customer")
    account_id = fields.Many2one('account.account',string='Account',default=get_account_default)
    start_date       = fields.Date(String='Start Date', required=True)
    end_date         = fields.Date(String='End Date')
    group_by_partner = fields.Boolean(string='Nhóm theo Khách Hàng')
    one_sheet        = fields.Boolean(string='Chung Sheet')


    @api.multi
    def print_report(self):
        return self.env['report'].get_action(self, 'cong_no_report.cong_no_report_template')

    @api.model
    def get_invalid_sale_order(self, force_null=False):
        self.ensure_one()

        conditions = [('state', '=', 'sale'), ('sale_order_return', '=', False)]
        if self.partner_ids and self.partner_ids.ids:
            conditions.append(('partner_id', 'in', self.partner_ids.ids))
        elif force_null:
            conditions.append(('partner_id', '=', False))

        if self.start_date:
            conditions.append(('date_order', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date_order', '<=', self.end_date))

        orders = self.env['sale.order'].search(conditions, order='date_order asc')
        return orders

    @api.model
    def get_invalid_purchase_order(self, force_null=False):
        self.ensure_one()

        conditions = [('state', '=', 'purchase'), ('purchase_order_return', '=', False)]
        if self.partner_ids and self.partner_ids.ids:
            conditions.append(('partner_id', 'in', self.partner_ids.ids))
        elif force_null:
            conditions.append(('partner_id', '=', False))

        if self.start_date:
            conditions.append(('date_order', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date_order', '<=', self.end_date))

        orders = self.env['purchase.order'].search(conditions, order='date_order asc')
        return orders

    # template = self.env.ref('auth_signup.reset_password_email')
    # assert template._name == 'mail.template'
    #
    # for user in self:
    #     if not user.email:
    #         raise UserError(_("Cannot send email: user %s has no email address.") % user.name)
    #     template.with_context(lang=user.lang).send_mail(user.id, force_send=True, raise_exception=True)
    #     _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)

    @api.multi
    def send_mail_report(self):
        partner_ids = self.partner_ids.ids
        for partner_id in partner_ids:
            partner_id = self.env['res.partner'].browse(partner_id)
            if partner_id.email:
                self.partner_ids = [(6,0,partner_id.ids)]
                self.partner_id = partner_id
                attachment = self.with_context(get_attachment=True).print_excel()
                template = self.env.ref('cong_no_report.send_mail_cong_no_report')
                template.write({
                    'attachment_ids' : [(4,attachment.id)]
                })
                template.send_mail(self.id,force_send=True, raise_exception=True)

    @api.multi
    def print_excel(self):
        self.ensure_one()

        if self.account_id and self.account_id.code == '131':
            order_ids = self.get_invalid_sale_order()
            no_invoice_orders = order_ids.filtered(lambda x: not x.invoice_ids.filtered(lambda inv: inv.state != 'cancel'))
            invalid_invoice_orders = order_ids.filtered(lambda x: x.invoice_ids and float_compare(x.amount_total, sum(x.invoice_ids.filtered(lambda x: x.state != 'cancel').mapped('amount_total')), 0) != 0)
            if no_invoice_orders or invalid_invoice_orders:
                return {
                    'name': 'Hoá đơn không hợp lệ',
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order.no.invoice',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context' : {
                        'no_invoice_order_ids' : no_invoice_orders.mapped('id'),
                        'invalid_order_line_ids' : invalid_invoice_orders.mapped('id'),
                    } ,
                }

        if self.account_id and self.account_id.code == '331':
            order_ids = self.get_invalid_purchase_order()
            no_invoice_orders = order_ids.filtered(lambda x: not x.invoice_ids.filtered(lambda inv: inv.state != 'cancel'))
            invalid_invoice_orders = order_ids.filtered(lambda x: x.invoice_ids and float_compare(x.amount_total, sum(x.invoice_ids.filtered(lambda x: x.state != 'cancel').mapped('amount_total')), 0) != 0)
            if no_invoice_orders or invalid_invoice_orders:
                return {
                    'name': 'Hoá đơn không hợp lệ',
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order.no.invoice',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('cong_no_report.purchase_order_no_invoice_form_view').id,
                    'target': 'new',
                    'context' : {
                        'no_invoice_purchase_order_ids' : no_invoice_orders.mapped('id'),
                        'invalid_purchase_order_line_ids' : invalid_invoice_orders.mapped('id'),
                    } ,
                }

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        if self.partner_ids:
            count = 0
            for partner_id in self.partner_ids:
                count += 1
                sheet_name          = '%s - %s' % (count, self.no_accent_vietnamese(partner_id.name, True))
                worksheet           = workbook.add_worksheet(sheet_name)
                data                = self.get_data_report(partner_id)
                data['order_lines'] = self.get_order_data(partner_id)
                self.write_data_to_sheet(workbook, worksheet, data)
        else:
            if not self.group_by_partner:
                worksheet = workbook.add_worksheet('Báo cáo tổng hợp')
                data = self.get_data_report(self.partner_id or False)
                self.write_data_to_sheet(workbook, worksheet, data)
            else:
                account_id = self.account_id and self.account_id.id or False
                if account_id:
                    account_id = self.env['account.account'].browse(account_id)
                else:
                    account_id = self.env['account.account'].search([
                        ('code', '=', '131')
                    ], limit=1)

                query_string = "SELECT DISTINCT partner_id FROM account_move_line WHERE account_id = %s ORDER BY partner_id" % (account_id.id)
                self.env.cr.execute(query_string)
                lines = self.env.cr.fetchall()

                if self.one_sheet:
                    worksheet = workbook.add_worksheet('Báo cáo tổng hợp')

                    # Write general data without lines
                    data = self.get_data_report(False)
                    data['data_line_report'] = []
                    start_line = self.write_data_to_sheet(workbook, worksheet, data)

                    for line in lines:
                        partner_id = line[0] or False
                        if partner_id:
                            partner = self.env['res.partner'].browse(partner_id)
                            data = self.get_data_report(partner)
                        else:
                            data = self.get_data_report(False, True)
                        start_line = self.write_data_to_sheet(workbook, worksheet, data, False, start_line + 1)
                else:
                    line_index = 0
                    for line in lines:
                        line_index += 1
                        partner_id = line[0] or False
                        if partner_id:
                            partner = self.env['res.partner'].browse(partner_id)
                            sheet_name = '%s - %s' % (line_index, self.no_accent_vietnamese(partner.name, True))
                            worksheet = workbook.add_worksheet(sheet_name)
                            data = self.get_data_report(partner)
                            data['order_lines'] = self.get_order_data(partner)
                            self.write_data_to_sheet(workbook, worksheet, data)
                        else:
                            worksheet = workbook.add_worksheet('Khác')
                            data = self.get_data_report(False, True)
                            data['order_lines'] = self.get_order_data(False, True)
                            self.write_data_to_sheet(workbook, worksheet, data)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'CongNoExcel.xlsx',
            'datas_fname': 'CongNoExcel.xlsx',
            'datas': result
        })

        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if 'get_attachment' in self._context:
            return attachment_id
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }

    def write_data_to_sheet(self, workbook, worksheet, data, show_header=True, start_line = 0):

        # merge_format = workbook.add_format({
        #     'bold': True,
        #     'align': 'center',
        #     'valign': 'vcenter',
        #     'font_size': '16'
        # })
        border_format = workbook.add_format({
            'border': 1
        })
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': 'dddddd',
        })
        header_border_format = workbook.add_format({
            'border': 1,
            'bg_color': 'dddddd',
        })
        body_bold_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter'
        })
        header_money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'bg_color': 'dddddd',
        })
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        number_format = workbook.add_format({
            'border': 1,
        })

        if show_header:
            header_label = "Báo cáo: %s" %(data['account'],)
            worksheet.merge_range('A1:I1', header_label.upper(), header_bold_color)

            worksheet.merge_range('A2:G2', "Kỳ báo cáo: ", body_bold_color)
            worksheet.write(start_line + 1, 7, "%s" %(self.start_date,), body_bold_color)
            worksheet.write(start_line + 1, 8, "%s" %(self.end_date or '',), body_bold_color)

            worksheet.merge_range('A3:G3', "Đối tác: ", body_bold_color)
            worksheet.write(start_line + 2, 7, "%s" % (data['name'],), body_bold_color)
            worksheet.write(start_line + 2, 8, '', body_bold_color)

            worksheet.merge_range('A4:G4', "Tài Khoản: %s" %(data['account'],), border_format)
            worksheet.write(start_line + 3, 7, "Nợ", border_format)
            worksheet.write(start_line + 3, 8, "Có", border_format)

            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 25)
            worksheet.set_column('D:D', 25)
            worksheet.set_column('E:E', 12)
            worksheet.set_column('F:F', 25)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 20)
            worksheet.set_column('I:I', 20)
            worksheet.set_column('J:J', 20)
            worksheet.set_column('K:K', 20)

            start_line += 4

        worksheet.merge_range('A%s:G%s' %(start_line + 1, start_line + 1), "Số dư đầu kỳ:", border_format)
        temp = data['no_before'] - data['co_before']
        temp_co_before = temp_no_before = 0
        if temp > 0:
            temp_no_before = temp
        else:
            temp_co_before = - temp
        worksheet.write(start_line, 7, temp_no_before, money)
        worksheet.write(start_line, 8, temp_co_before, money)

        worksheet.merge_range('A%s:G%s' %(start_line + 2, start_line + 2), "Tổng phát sinh trong kỳ:", border_format)
        worksheet.write(start_line + 1, 7, data['no_current'], money)
        worksheet.write(start_line + 1, 8, data['co_current'], money)

        worksheet.merge_range('A%s:G%s' %(start_line + 3, start_line + 3), "Số dư cuối kỳ:", border_format)
        worksheet.write(start_line + 2, 7, data['no_end'], money)
        worksheet.write(start_line + 2, 8, data['co_end'], money)

        cong_no_label = 'CÔNG NỢ TỔNG HỢP'
        worksheet.merge_range(start_line + 4, 0, start_line + 4, 8, cong_no_label, header_bold_color)
        worksheet.merge_range('A%s:A%s' % (start_line + 6, start_line + 7), "Ngày hạch toán", header_border_format)
        worksheet.merge_range('B%s:B%s' % (start_line + 6, start_line + 7), "Ngày chứng từ", header_border_format)
        worksheet.merge_range('C%s:C%s' % (start_line + 6, start_line + 7), "Số chứng từ", header_border_format)
        worksheet.merge_range('D%s:D%s' % (start_line + 6, start_line + 7), "Diễn giải", header_border_format)
        worksheet.merge_range('E%s:E%s' % (start_line + 6, start_line + 7), "TK công nợ", header_border_format)
        worksheet.merge_range('F%s:G%s' % (start_line + 6, start_line + 6), "Phát sinh", header_border_format)
        worksheet.merge_range('H%s:I%s' % (start_line + 6, start_line + 6), "Số dư	", header_border_format)
        worksheet.write(start_line + 6, 5, "Nợ", header_border_format)
        worksheet.write(start_line + 6, 6, "Có", header_border_format)
        worksheet.write(start_line + 6, 7, "Nợ", header_border_format)
        worksheet.write(start_line + 6, 8, "Có", header_border_format)

        worksheet.write(start_line + 7, 3, 'Số dư đầu kỳ', border_format)
        worksheet.write(start_line + 7, 4, data['account_code'], border_format)
        worksheet.write(start_line + 7, 5, 0, money)
        worksheet.write(start_line + 7, 6, 0, money)
        worksheet.write(start_line + 7, 7, temp_no_before, money)
        worksheet.write(start_line + 7, 8, temp_co_before, money)

        no_before = temp_no_before
        co_before = temp_co_before
        row       = start_line + 8
        count     = 0
        for line in data['cong_no_report']:
        #     no    += 1
            count += 1
            if no_before > 0:
                no_before += (line['debit'] - line['credit'])
                if no_before < 0:
                    co_before -= no_before
                    no_before  = 0
            elif co_before > 0:
                co_before += (line['credit'] - line['debit'])
                if co_before < 0:
                    no_before -= co_before
                    co_before  = 0
            else:
                no_before += (line['debit'] - line['credit'])
                if no_before < 0:
                    co_before -= no_before
                    no_before  = 0
            line_name = line['name']
            if line_name == '/':
                if line['ref'].find('SO') != -1:
                    line_name = 'Bán hàng'
                elif line['ref'].find('RT0') != -1:
                    line_name = 'Trả hàng'
                elif line['ref'].find('PO') != -1:
                    line_name = 'Mua hàng'
                elif line['ref'].find('RTP') != -1:
                    line_name = 'Trả hàng mua'

            if line['credit']:
                worksheet.write(row, 0, line['date'], header_border_format)
                worksheet.write(row, 1, line['date'], header_border_format)
                worksheet.write(row, 2, line['ref'], header_border_format)
                worksheet.write(row, 3, line_name, header_border_format)
                worksheet.write(row, 4, data['account_code'] or '', header_border_format)
                worksheet.write(row, 5, line['debit'], header_money)
                worksheet.write(row, 6, line['credit'], header_money)
                worksheet.write(row, 7, no_before, header_money)
                worksheet.write(row, 8, co_before, header_money)
            else:
                worksheet.write(row, 0, line['date'], border_format)
                worksheet.write(row, 1, line['date'], border_format)
                worksheet.write(row, 2, line['ref'], border_format)
                worksheet.write(row, 3, line_name, border_format)
                worksheet.write(row, 4, data['account_code'] or '', border_format)
                worksheet.write(row, 5, line['debit'], money)
                worksheet.write(row, 6, line['credit'], money)
                worksheet.write(row, 7, no_before, money)
                worksheet.write(row, 8, co_before, money)
            row += 1

        start_line = row + 1

        sale_label = 'CÔNG NỢ CHI TIẾT'
        worksheet.merge_range(start_line, 0, start_line, 10, sale_label, header_bold_color)
        start_line += 1

        if show_header:
            worksheet.merge_range('A%s:A%s' % (start_line + 1, start_line + 2), "Ngày hạch toán", header_border_format)
            worksheet.merge_range('B%s:B%s' % (start_line + 1, start_line + 2), "Ngày chứng từ", header_border_format)
            worksheet.merge_range('C%s:C%s' % (start_line + 1, start_line + 2), "Số chứng từ", header_border_format)
            worksheet.merge_range('D%s:D%s' % (start_line + 1, start_line + 2), "Diễn giải", header_border_format)
            worksheet.merge_range('E%s:E%s' % (start_line + 1, start_line + 2), "Mã hàng", header_border_format)
            worksheet.merge_range('F%s:F%s' % (start_line + 1, start_line + 2), "TK công nợ", header_border_format)
            worksheet.merge_range('G%s:G%s' % (start_line + 1, start_line + 2), "TK đối ứng", header_border_format)
            worksheet.merge_range('H%s:I%s' % (start_line + 1, start_line + 1), "Phát sinh", header_border_format)
            worksheet.merge_range('J%s:K%s' % (start_line + 1, start_line + 1), "Số dư	", header_border_format)
            worksheet.write(start_line + 1, 7, "Nợ", header_border_format)
            worksheet.write(start_line + 1, 8, "Có", header_border_format)
            worksheet.write(start_line + 1, 9, "Nợ", header_border_format)
            worksheet.write(start_line + 1, 10, "Có", header_border_format)

            start_line += 2

        worksheet.write(start_line, 0, 'Đối tác: %s' %(data['name'],), border_format)
        worksheet.write(start_line, 7, data['no_current'], money)
        worksheet.write(start_line, 8, data['co_current'], money)
        start_line += 1

        worksheet.write(start_line, 3, 'Số dư đầu kỳ', border_format)
        worksheet.write(start_line, 4, '', border_format)
        worksheet.write(start_line, 5, data['account_code'], border_format)
        worksheet.write(start_line, 6, '', border_format)
        worksheet.write(start_line, 7, 0, money)
        worksheet.write(start_line, 8, 0, money)
        worksheet.write(start_line, 9, temp_no_before, money)
        worksheet.write(start_line, 10, temp_co_before, money)
        start_line += 1

        vat_lines = []

        row   = start_line
        # no_before = data['no_before']
        # co_before = data['co_before']
        no_before = temp_no_before
        co_before = temp_co_before
        count = 0
        # no    = 0
        for line in data['data_line_report']:
        #     no    += 1
            count += 1
            if no_before > 0:
                no_before += (line['debit'] - line['credit'])
                if no_before < 0:
                    co_before -= no_before
                    no_before  = 0
            elif co_before > 0:
                co_before += (line['credit'] - line['debit'])
                if co_before < 0:
                    no_before -= co_before
                    co_before  = 0
            else:
                no_before += (line['debit'] - line['credit'])
                if no_before < 0:
                    co_before -= no_before
                    no_before  = 0
            if line['credit']:
                worksheet.write(row, 0, line['date'], header_border_format)
                worksheet.write(row, 1, line['date'], header_border_format)
                worksheet.write(row, 2, line['ref'], header_border_format)
                worksheet.write(row, 3, line['name'], header_border_format)
                worksheet.write(row, 4, line['product_code'], header_border_format)
                worksheet.write(row, 5, data['account_code'] or '', header_border_format)
                worksheet.write(row, 6, line['account_id'], header_border_format)
                worksheet.write(row, 7, line['debit'], header_money)
                worksheet.write(row, 8, line['credit'], header_money)
                worksheet.write(row, 9, no_before, header_money)
                worksheet.write(row, 10, co_before, header_money)
            else:
                line_style = border_format
                line_money_style = money
                if line['account_id'] == '33311':
                    vat_lines.append(line)

                    line_style = header_border_format
                    line_money_style = header_money

                worksheet.write(row, 0, line['date'], line_style)
                worksheet.write(row, 1, line['date'], line_style)
                worksheet.write(row, 2, line['ref'], line_style)
                worksheet.write(row, 3, line['name'], line_style)
                worksheet.write(row, 4, line['product_code'], line_style)
                worksheet.write(row, 5, data['account_code'] or '', line_style)
                worksheet.write(row, 6, line['account_id'], line_style)
                worksheet.write(row, 7, line['debit'], line_money_style)
                worksheet.write(row, 8, line['credit'], line_money_style)
                worksheet.write(row, 9, no_before, line_money_style)
                worksheet.write(row, 10, co_before, line_money_style)
            row += 1

        start_line += count

        if data['order_lines'] and len(data['order_lines']) > 0:
            sale_label = 'CHI TIẾT HÀNG HOÁ'
            worksheet.merge_range(start_line + 1, 0, start_line + 1, 8, sale_label, header_bold_color)

            start_line += 1
            worksheet.write(start_line + 1, 0, 'Ngày', header_border_format)
            worksheet.write(start_line + 1, 1, 'Số đơn hàng', header_border_format)
            worksheet.write(start_line + 1, 2, 'Mã hàng', header_border_format)
            worksheet.write(start_line + 1, 3, 'Tên hàng', header_border_format)
            worksheet.write(start_line + 1, 4, 'ĐVT', header_border_format)
            worksheet.write(start_line + 1, 5, 'SL', header_border_format)
            worksheet.write(start_line + 1, 6, 'Đơn giá (giá in ra phiếu xuất)', header_border_format)
            worksheet.write(start_line + 1, 7, 'VAT', header_border_format)
            worksheet.write(start_line + 1, 8, 'Tổng', header_border_format)

            row = start_line + 2
            price_subtotal = 0
            for order_line in data['order_lines']:
                if self.account_id.code == '131':
                    price_unit = order_line.price_subtotal / order_line.product_uom_qty
                    if order_line.order_id.sale_order_return:
                        worksheet.write(row, 0, order_line.date_order, border_format)
                        worksheet.write(row, 1, order_line.order_id.name, border_format)
                        worksheet.write(row, 2, order_line.product_id.default_code, border_format)
                        worksheet.write(row, 3, order_line.product_id.name, border_format)
                        worksheet.write(row, 4, order_line.product_uom.name, border_format)
                        worksheet.write(row, 5, - order_line.product_uom_qty, border_format)
                        worksheet.write(row, 6, price_unit, money)
                        worksheet.write(row, 7, order_line.tax_sub, border_format)
                        worksheet.write(row, 8, - order_line.price_subtotal, money)
                        price_subtotal -= order_line.price_subtotal
                    else:
                        worksheet.write(row, 0, order_line.date_order, border_format)
                        worksheet.write(row, 1, order_line.order_id.name, border_format)
                        worksheet.write(row, 2, order_line.product_id.default_code, border_format)
                        worksheet.write(row, 3, order_line.product_id.name, border_format)
                        worksheet.write(row, 4, order_line.product_uom.name, border_format)
                        worksheet.write(row, 5, order_line.product_uom_qty, border_format)
                        worksheet.write(row, 6, price_unit, money)
                        worksheet.write(row, 7, order_line.tax_sub, border_format)
                        worksheet.write(row, 8, order_line.price_subtotal, money)
                        price_subtotal += order_line.price_subtotal
                elif self.account_id.code == '331':
                    price_unit = order_line.price_subtotal / order_line.product_qty
                    if order_line.order_id.purchase_order_return:
                        worksheet.write(row, 0, order_line.date_planned, border_format)
                        worksheet.write(row, 1, order_line.order_id.name, border_format)
                        worksheet.write(row, 2, order_line.product_id.default_code, border_format)
                        worksheet.write(row, 3, order_line.product_id.name, border_format)
                        worksheet.write(row, 4, order_line.product_uom.name, border_format)
                        worksheet.write(row, 5, - order_line.product_qty, border_format)
                        worksheet.write(row, 6, price_unit, money)
                        worksheet.write(row, 7, order_line.tax_sub, border_format)
                        worksheet.write(row, 8, - order_line.price_subtotal, money)
                        price_subtotal -= order_line.price_subtotal
                    else:
                        worksheet.write(row, 0, order_line.date_planned, border_format)
                        worksheet.write(row, 1, order_line.order_id.name, border_format)
                        worksheet.write(row, 2, order_line.product_id.default_code, border_format)
                        worksheet.write(row, 3, order_line.product_id.name, border_format)
                        worksheet.write(row, 4, order_line.product_uom.name, border_format)
                        worksheet.write(row, 5, order_line.product_qty, border_format)
                        worksheet.write(row, 6, price_unit, money)
                        worksheet.write(row, 7, order_line.tax_sub, border_format)
                        worksheet.write(row, 8, order_line.price_subtotal, money)
                        price_subtotal += order_line.price_subtotal
                row += 1

            worksheet.merge_range(row, 0, row, 7, 'Tổng', header_bold_color)
            worksheet.write(row, 8, price_subtotal, header_money)
        #
        # worksheet.set_column('B:B', None, None, {'hidden': True})
        # worksheet.set_column('C:C', None, None, {'hidden': True})
        # worksheet.set_column('D:D', None, None, {'hidden': True})
        # worksheet.set_column('E:E', None, None, {'hidden': True})
        # worksheet.set_column('G:G', None, None, {'hidden': True})
        # worksheet.set_column('J:J', None, None, {'hidden': True})

        start_line = row + 2

        if len(vat_lines) > 0:
            sale_label = 'VAT'
            worksheet.merge_range(start_line, 0, start_line, 8, sale_label, header_bold_color)
            start_line += 1

            worksheet.merge_range('A%s:A%s' % (start_line + 1, start_line + 2), "Ngày hạch toán",
                                  header_border_format)
            worksheet.merge_range('B%s:B%s' % (start_line + 1, start_line + 2), "Ngày chứng từ",
                                  header_border_format)
            worksheet.merge_range('C%s:C%s' % (start_line + 1, start_line + 2), "Số chứng từ", header_border_format)
            worksheet.merge_range('D%s:D%s' % (start_line + 1, start_line + 2), "Diễn giải", header_border_format)
            worksheet.merge_range('E%s:E%s' % (start_line + 1, start_line + 2), "Mã hàng", header_border_format)
            worksheet.merge_range('F%s:F%s' % (start_line + 1, start_line + 2), "TK công nợ", header_border_format)
            worksheet.merge_range('G%s:G%s' % (start_line + 1, start_line + 2), "TK đối ứng", header_border_format)
            worksheet.merge_range('H%s:I%s' % (start_line + 1, start_line + 1), "Phát sinh", header_border_format)
            worksheet.write(start_line + 1, 7, "Nợ", header_border_format)
            worksheet.write(start_line + 1, 8, "Có", header_border_format)

            total_debit = 0
            total_credit = 0
            row = start_line + 2
            for line in vat_lines:
                worksheet.write(row, 0, line['date'], header_border_format)
                worksheet.write(row, 1, line['date'], header_border_format)
                worksheet.write(row, 2, line['ref'], header_border_format)
                worksheet.write(row, 3, line['name'], header_border_format)
                worksheet.write(row, 4, line['product_code'], header_border_format)
                worksheet.write(row, 5, data['account_code'] or '', header_border_format)
                worksheet.write(row, 6, line['account_id'], header_border_format)
                worksheet.write(row, 7, line['debit'], header_money)
                worksheet.write(row, 8, line['credit'], header_money)
                total_debit += line['debit']
                total_credit += line['credit']

                row += 1

            worksheet.merge_range(row, 0, row, 6, 'Tổng', header_bold_color)
            worksheet.write(row, 7, total_debit, header_money)
            worksheet.write(row, 8, total_credit, header_money)

        return start_line

    def round_number(self, number):
        return number
        # return math.floor(number / 100) * 100

    def no_accent_vietnamese(self, s, truncate=False):
        # s = s.decode('utf-8')
        # s = re.sub(u'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
        # s = re.sub(u'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
        # s = re.sub(u'èéẹẻẽêềếệểễ', 'e', s)
        # s = re.sub(u'ÈÉẸẺẼÊỀẾỆỂỄ', 'E', s)
        # s = re.sub(u'òóọỏõôồốộổỗơờớợởỡ', 'o', s)
        # s = re.sub(u'ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ', 'O', s)
        # s = re.sub(u'ìíịỉĩ', 'i', s)
        # s = re.sub(u'ÌÍỊỈĨ', 'I', s)
        # s = re.sub(u'ùúụủũưừứựửữ', 'u', s)
        # s = re.sub(u'ƯỪỨỰỬỮÙÚỤỦŨ', 'U', s)
        # s = re.sub(u'ỳýỵỷỹ', 'y', s)
        # s = re.sub(u'ỲÝỴỶỸ', 'Y', s)
        # s = re.sub(u'Đ', 'D', s)
        # s = re.sub(u'đ', 'd', s)
        if truncate:
            if len(s) > 25:
                names = s.split(' ')
                length = len(names) - 4
                if length > 0:
                    s = ' '.join(names[length:])
        return s # .encode('utf-8')

    @api.model
    def get_order_data(self, partner, force_null=True):
        self.ensure_one()

        conditions = []
        if partner and partner.id:
            conditions.append(('order_partner_id', '=', partner.id))
        elif force_null:
            conditions.append(('order_partner_id', '=', False))

        order_lines = []
        if self.account_id.code == '131':
            conditions.append(('state', '=', 'sale'))
            if self.start_date:
                conditions.append(('date_order', '>=', self.start_date))
            if self.end_date:
                conditions.append(('date_order', '<=', self.end_date))
            order_lines = self.env['sale.order.line'].search(conditions, order='date_order asc')
        elif self.account_id.code == '331':
            conditions.append(('state', '=', 'purchase'))
            if self.start_date:
                conditions.append(('date_planned', '>=', self.start_date))
            if self.end_date:
                conditions.append(('date_planned', '<=', self.end_date))
            order_lines = self.env['purchase.order.line'].search(conditions, order='date_planned asc')

        return order_lines

    @api.model
    def get_data_report(self, partner, force_null=False):
        self.ensure_one()

        data = {
            'ids': self.ids,
            'model': 'cong.no.report',
            'from': self.read(['start_date', 'end_date', 'partner_id', 'account_id'])[0]
        }
        account_id = data['from']['account_id']
        if account_id:
            account_id = self.env['account.account'].browse(account_id[0])
        else:
            account_id = self.env['account.account'].search([
                ('code', '=', '131')
            ], limit=1)

        account_code = account_id.code

        conditions = [('account_id.code', '=', account_code)]
        conditions_before = [('account_id.code', '=', account_code)]
        if data['from']['start_date']:
            conditions.append(('date', '>=', data['from']['start_date']))
            conditions_before.append(('date', '<', data['from']['start_date']))
        if data['from']['end_date']:
            conditions.append(('date', '<=', data['from']['end_date']))
        #
        if partner:
            conditions.append(('partner_id', '=', partner.id))
            conditions_before.append(('partner_id', '=', partner.id))
        elif force_null:
            conditions.append(('partner_id', '=', False))
            conditions_before.append(('partner_id', '=', False))

        no_before = 0.0
        co_before = 0.0
        if data['from']['start_date']:
            lines = self.env['account.move.line'].search(conditions_before, order='date asc')
            for line in lines:
                if line.account_id.code == account_code:
                    no_before += line.debit
                    co_before += line.credit

        no_before = self.round_number(no_before)
        co_before = self.round_number(co_before)

        no_current = 0.0
        co_current = 0.0
        cong_no_report = []
        data_line_report = []
        moves = self.env['account.move.line'].search(conditions, order='date asc').mapped('move_id')
        for account_move in moves:
            line_current_account = False
            for data_line in account_move.line_ids:
                if partner:
                    if data_line.account_id.code == account_code and data_line.partner_id == partner:
                        no_current += data_line.debit
                        co_current += data_line.credit

                        list = {
                            'date': data_line.date,
                            'move_id': data_line.move_id.name,
                            'journal_id': data_line.journal_id.display_name,
                            'name': data_line.name,
                            'ref': data_line.ref or account_move.name,
                            'partner_id': data_line.partner_id.name,
                            'account_id': data_line.account_id.code,
                            'debit': data_line.debit,
                            'credit': data_line.credit,
                            'date_maturity': data_line.date_maturity,
                            'product_id': data_line.product_id,
                            'product_code': data_line.product_id and data_line.product_id.default_code or '',
                        }
                        cong_no_report.append(list)
                        line_current_account = list
                else:
                    if data_line.account_id.code == account_code:
                        no_current += data_line.debit
                        co_current += data_line.credit

                        list = {
                            'date': data_line.date,
                            'move_id': data_line.move_id.name,
                            'journal_id': data_line.journal_id.display_name,
                            'name': data_line.name,
                            'ref': data_line.ref or account_move.name,
                            'partner_id': data_line.partner_id.name,
                            'account_id': data_line.account_id.code,
                            'debit': data_line.debit,
                            'credit': data_line.credit,
                            'date_maturity': data_line.date_maturity,
                            'product_id': data_line.product_id,
                            'product_code': data_line.product_id and data_line.product_id.default_code or '',
                        }
                        cong_no_report.append(list)
                        line_current_account = list
            for data_line in account_move.line_ids:
                if data_line.account_id.code != account_code:
                    if (line_current_account.get('debit', 0) and data_line.credit):
                        list = {
                            'date' : data_line.date,
                            'move_id' : data_line.move_id.name,
                            'journal_id' : data_line.journal_id.display_name,
                            'name' : data_line.name,
                            'ref' : data_line.ref or account_move.name,
                            'partner_id' : data_line.partner_id.name,
                            'account_id' : data_line.account_id.code,
                            'debit' : data_line.credit if data_line.credit <= line_current_account.get('debit') else line_current_account.get('debit'),
                            'credit' : data_line.debit,
                            'date_maturity' : data_line.date_maturity,
                            'product_id': data_line.product_id,
                            'product_code': data_line.product_id and data_line.product_id.default_code or '',
                        }
                        data_line_report.append(list)
                    elif (line_current_account.get('credit', 0) and data_line.debit):
                        list = {
                            'date': data_line.date,
                            'move_id': data_line.move_id.name,
                            'journal_id': data_line.journal_id.display_name,
                            'name': data_line.name,
                            'ref': data_line.ref or account_move.name,
                            'partner_id': data_line.partner_id.name,
                            'account_id': data_line.account_id.code,
                            'debit': data_line.credit,
                            'credit': data_line.debit if data_line.debit <= line_current_account.get('credit') else line_current_account.get('credit'),
                            'date_maturity': data_line.date_maturity,
                            'product_id': data_line.product_id,
                            'product_code': data_line.product_id and data_line.product_id.default_code or '',
                        }
                        data_line_report.append(list)

        no_current = self.round_number(no_current)
        co_current = self.round_number(co_current)

        no_end = 0.0
        co_end = 0.0
        sum_cong_no = no_before + no_current - co_before - co_current
        if sum_cong_no < 0:
            co_end = - sum_cong_no
        else:
            no_end = sum_cong_no

        no_end = self.round_number(no_end)
        co_end = self.round_number(co_end)

        return {
            'name'             : partner and partner.name or '',
            'account'          : account_id.display_name,
            'account_code'     : account_id.code,
            'no_before'        : no_before,
            'co_before'        : co_before,
            'no_current'       : no_current,
            'co_current'       : co_current,
            'no_end'           : no_end,
            'co_end'           : co_end,
            'data_line_report' : data_line_report,
            'cong_no_report'   : cong_no_report,
            'order_lines'      : [],
        }