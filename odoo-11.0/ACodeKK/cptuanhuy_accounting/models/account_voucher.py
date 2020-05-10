# -*- coding: utf-8 -*-

from odoo import models, fields, api
import math
import base64
import StringIO
import xlsxwriter
import os
from datetime import datetime

class account_vourcher_line_inherit(models.Model):
    _inherit = 'account.voucher.line'

    sale_id = fields.Many2one('sale.order', string='Đơn hàng')
    purchase_id = fields.Many2one('purchase.order', string='Đơn Mua hàng')

class account_vourcher_inherit(models.Model):
    _inherit = 'account.voucher'

    bank_id             = fields.Many2one(domain=[('bank','=',True), ('bank_type', '=', 'internal')])
    check_bank_id       = fields.Boolean(compute='_get_check_bank_id')
    project_id          = fields.Many2one('project.project', string="Dự án")
    contract_id         = fields.Many2one('account.analytic.account', string="Hợp đồng")
    tai_khoan_giao_dich = fields.Char(string='Tài khoản giao dịch')
    sale_id             = fields.Many2many('sale.order', string='Đơn hàng')
    purchase_id         = fields.Many2many('purchase.order', string='Đơn Mua hàng')
    sale_ids            = fields.Many2many('sale.order','voucher_sale_lines_rel','voucher_id','sale_id', string='Đơn hàng',compute='get_sale_ids_from_line')
    purchase_ids        = fields.Many2many('purchase.order','voucher_purchase_lines_rel','voucher_id','purchase_id', string='Đơn Mua hàng',compute='get_purchase_ids_from_line')

    @api.depends('line_ids.sale_id')
    def get_sale_ids_from_line(self):
        for record in self:
            record.sale_ids = record.line_ids.mapped('sale_id')

    @api.depends('line_ids.purchase_id')
    def get_purchase_ids_from_line(self):
        for record in self:
            record.purchase_ids = record.line_ids.mapped('purchase_id')

    def _get_number_voucher(self):
        phieuthu_action  = self.env.ref('account_voucher.action_sale_receipt')
        phieuchi_action = self.env.ref('account_voucher.action_purchase_receipt')
        cur_year = str(datetime.now().year)
        cur_year = cur_year[-2:]
        if self._context and 'params' in self._context and 'action' in self._context['params']:
            if self._context['params'].get('action') == phieuchi_action.id:
                phieuchi_ids = self.env['account.voucher'].search([
                    ('journal_id.type', '=', 'purchase'),
                    ('voucher_type', '=', 'purchase'),
                    ('number_voucher', '!=', False)
                ], order="id desc")
                phieuchi = False
                for phieuchi_id in phieuchi_ids:
                    if '/%s'%(cur_year) in phieuchi_id.number_voucher:
                        phieuchi = phieuchi_id
                        break
                number = 0
                if phieuchi and phieuchi.number_voucher:
                    try:
                        number = int(phieuchi.number_voucher.split("/")[0])
                    except:
                        pass
                else:
                    number = 0
                return str(number + 1) + "/%s"%(cur_year)
            elif self._context['params'].get('action') == phieuthu_action.id:
                phieuthu_ids = self.env['account.voucher'].search([
                    ('journal_id.type', '=', 'sale'),
                    ('voucher_type', '=', 'sale'),
                    ('number_voucher', '!=', False)
                ], order="id desc")
                phieuthu = False
                for phieuthu_id in phieuthu_ids:
                    if '/%s'%(cur_year) in phieuthu_id.number_voucher:
                        phieuthu = phieuthu_id
                        break
                number = 0
                if phieuthu and phieuthu.number_voucher:
                    try:
                        number = int(phieuthu.number_voucher.split("/")[0])
                    except:
                        pass
                else:
                    number = 0
                return str(number + 1) + "/%s"%(cur_year)

    number_voucher = fields.Char(string="Number Voucher", default=_get_number_voucher)

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            self.contract_id = self.project_id.analytic_account_id
            return {'domain': {'contract_id': [('id','in',self.project_id.analytic_account_id.ids)]}}
        else:
            return {'domain': {'contract_id': [()]}}

    @api.multi
    def proforma_voucher(self):
        res = super(account_vourcher_inherit, self).proforma_voucher()
        for record in self:
            if record.contract_id:
                record.contract_id.check_payment = True
            account_guarantee_id = self.env['account.guarantee'].search([('unc_id','=',record.id)])
            if account_guarantee_id and account_guarantee_id.account_analytic_account_id:
                account_guarantee_id.account_analytic_account_id.check_guarantee = True
        return res

    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        for line in self.line_ids:
            # create one move line per voucher line where amount is not 0.0
            if not line.price_subtotal:
                continue
            line_subtotal = line.price_subtotal
            if self.voucher_type == 'sale':
                line_subtotal = -1 * line.price_subtotal
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context,
            # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(line.price_unit * line.quantity)
            move_line = {
                'journal_id': self.journal_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': self.partner_id.commercial_partner_id.id,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': abs(amount) if self.voucher_type == 'sale' else 0.0,
                'debit': abs(amount) if self.voucher_type == 'purchase' else 0.0,
                'date': self.account_date,
                'tax_ids': [(4, t.id) for t in line.tax_ids],
                'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
                'currency_id': company_currency != current_currency and current_currency or False,
                'payment_id': self._context.get('payment_id'),
            #     add sale_id here
                'sale_id': line.sale_id.id or False,
            }
            self.env['account.move.line'].with_context(apply_taxes=True).create(move_line)
        return line_total

    @api.multi
    def cancel_voucher(self):
        res = super(account_vourcher_inherit, self).cancel_voucher()
        for record in self:
            if record.contract_id:
                record.contract_id.check_payment = False
            account_guarantee_id = self.env['account.guarantee'].search([('unc_id','=',record.id)])
            if account_guarantee_id and account_guarantee_id.account_analytic_account_id:
                account_guarantee_id.account_analytic_account_id.check_guarantee = False
        return res



    @api.onchange('bank_id')
    def _get_check_bank_id(self):
        ab_bank = self.env.ref('cptuanhuy_accounting.partner_bank_anbinh_cndanang')
        tp_bank = self.env.ref('cptuanhuy_accounting.partner_bank_tienphong_cndanang')
        tc_bank = self.env.ref('cptuanhuy_accounting.partner_bank_teckcom_cndanang')
        domain = [ab_bank.id, tp_bank.id, tc_bank.id]
        if self.bank_id.id in domain:
            self.check_bank_id = True
        else:
            self.check_bank_id = False

    @api.multi
    def print_unc_bank(self):
        self.ensure_one()
        ab_bank = self.env.ref('cptuanhuy_accounting.partner_bank_anbinh_cndanang')
        if self.bank_id == ab_bank:
            return self.env['report'].get_action(self, 'account_bank_voucher.account_voucher_unc_template')

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        unc_sheet = workbook.add_worksheet('UNC')
        tp_bank = self.env.ref('cptuanhuy_accounting.partner_bank_tienphong_cndanang')
        tc_bank = self.env.ref('cptuanhuy_accounting.partner_bank_teckcom_cndanang')
        if self.bank_id == tp_bank:
            self.create_unc_tp_bank(unc_sheet, workbook)
        elif self.bank_id == tc_bank:
            self.create_unc_tc_bank(unc_sheet, workbook)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'UNC.xlsx', 'datas_fname': 'UNC.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    def create_unc_tp_bank(self,worksheet,workbook):
        tp_bank_logo = os.path.abspath(__file__).split('models')[0] + 'data/tp_bank_logo.jpg'
        tp_header_line = os.path.abspath(__file__).split('models')[0] + 'data/tp_header_line.jpg'
        header_body_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'right',
            'font_color': '#E97941',
            'valign': 'vcenter',
        })

        payment_order_format = workbook.add_format({
            'font_size': '11',
            'align': 'right',
            'valign': 'vcenter',
        })

        header_body_color_bg_tim = workbook.add_format({
            # 'bold': True,
            'font_size': '9',
            'align': 'left',
            'bg_color': '#D5A4FE',
            'valign': 'vcenter',
        })

        bold = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'bg_color': '#D5A4FE',
            'valign': 'vcenter',
            'bold': True,
        })
        italic = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'bg_color': '#D5A4FE',
            'valign': 'vcenter',
            'italic': True,
        })

        body_format = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
        })

        body_format_bold = workbook.add_format({
            'bold': True,
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
        })

        body_format_number = workbook.add_format({
            'font_size': '9',
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0',
        })

        body_format_text_wrap = workbook.add_format({
            'font_size': '9',
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        body_format_text_wrap_mr_top = workbook.add_format({
            'font_size': '9',
            'align': 'center',
            'valign': 'top',
            'text_wrap': True,
        })

        body_format_text_wrap_left = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        body_format_text_wrap_left_top = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'valign': 'top',
            'text_wrap': True,
        })

        body_format_red_color = workbook.add_format({
            'bold': True,
            'font_size': '9',
            'align': 'left',
            'font_color': '#E97941',
            'valign': 'vcenter',
        })

        body_format_red_color_center = workbook.add_format({
            'bold': True,
            'font_size': '9',
            'align': 'center',
            'font_color': '#E97941',
            'valign': 'vcenter',
        })

        worksheet.set_row(2, 4)
        worksheet.set_row(3, 4)
        worksheet.set_row(7, 30)
        worksheet.set_row(9, 30)
        worksheet.set_row(10, 30)
        worksheet.set_row(11, 25)
        worksheet.set_row(12, 15)
        worksheet.set_row(13, 15)
        worksheet.set_row(14, 25)
        worksheet.set_row(15, 10)
        worksheet.set_row(16, 10)
        worksheet.set_row(17, 10)
        worksheet.set_row(18, 10)

        worksheet.set_column('A:A', None, None, {'hidden': True})
        worksheet.set_column('B:C', 12)
        worksheet.set_column('D:D', 7)
        worksheet.set_column('E:E', 5)
        worksheet.set_column('F:F', 11)
        worksheet.set_column('G:H', 9)
        worksheet.set_column('J:L', 8)
        worksheet.set_column('M:M', 14)
        worksheet.set_column('I:I', None, None, {'hidden': True})

        worksheet.merge_range('B1:C2', "")
        worksheet.insert_image('B1', tp_bank_logo, {'y_offset': 5, 'x_scale': 0.99, 'y_scale': 1.1})

        worksheet.merge_range('B3:M4', "")
        worksheet.insert_image('B3', tp_header_line, {'x_scale': 0.98, 'y_scale': 0.95})

        worksheet.merge_range('H1:M1', unicode("ỦY NHIỆM CHI", "utf-8"),header_body_color)
        worksheet.merge_range('F2:M2', unicode("PAYMENT ORDER", "utf-8"),payment_order_format)

        worksheet.merge_range('B5:D5', "", header_body_color_bg_tim)
        worksheet.write_rich_string('B5',bold,unicode("Đề nghị ghi nợ tài khoản ", 'utf-8'),'(',italic,'Please debit acount',')',header_body_color_bg_tim)
        worksheet.write('E5','', header_body_color_bg_tim)
        worksheet.write('F5','', header_body_color_bg_tim)
        worksheet.merge_range('G5:H5', "",header_body_color_bg_tim)
        worksheet.write_rich_string('G5', bold, unicode("Ngày", "utf-8"), italic,
                                    ' (Date): 18/12/2018',header_body_color_bg_tim)
        worksheet.merge_range('J5:M5',"",header_body_color_bg_tim)
        worksheet.write_rich_string('J5', bold, unicode("Số tiền ", "utf-8"), italic,
                                    '(With amount)',header_body_color_bg_tim)

        worksheet.merge_range('B6:C6', unicode("Tên tài khoản (Account name):", "utf-8"),body_format)
        worksheet.merge_range('D6:H6', unicode("NGÔ THỊ THIÊN", "utf-8"), body_format_red_color)
        worksheet.write('K6',unicode("£ VND", "utf-8"), body_format)
        worksheet.merge_range('L6:M6', unicode("o EUR", "utf-8"), body_format)

        worksheet.merge_range('J6:J7', unicode("Loại tiền (Currency):", "utf-8"), body_format_text_wrap)

        worksheet.merge_range('B7:C7', unicode("Số tài khoản (Account number)", "utf-8"), body_format)
        worksheet.merge_range('D7:H7', unicode(str(self.acc_number) or "", "utf-8"), body_format_red_color_center)
        worksheet.write('K7', unicode("£ USD", "utf-8"), body_format)
        worksheet.merge_range('L7:M7', unicode("o Khác (Other)", "utf-8"), body_format)

        worksheet.write('B8', unicode("Ngân hàng:     (With bank)", "utf-8"), body_format_text_wrap_left)
        worksheet.merge_range('C8:E8', unicode("TPBANK", "utf-8"), body_format)
        worksheet.write('F8', unicode("Tỉnh/TP: (Provinces/City)", "utf-8"), body_format_text_wrap_left)
        worksheet.merge_range('G8:H8', unicode("DNG", "utf-8"), body_format)
        worksheet.merge_range('J8:M8', unicode("Số tiền bằng số (Amount in figures)", "utf-8"), body_format_text_wrap_left_top)

        worksheet.merge_range('B9:H9', "", header_body_color_bg_tim)
        worksheet.write_rich_string('B9', bold, unicode("Người hưởng (Beneficiary)", "utf-8"), header_body_color_bg_tim)
        worksheet.merge_range('J9:L9', self.amount,
                              body_format_number)
        worksheet.write('M9', unicode("VND", "utf-8"), body_format)

        worksheet.merge_range('B10:C10', unicode("Tên tài khoản (Account name):", "utf-8"),
                              body_format)
        worksheet.merge_range('D10:H10', unicode("Danh sách đính kèm", "utf-8"),
                              body_format_red_color)
        worksheet.merge_range('J10:M10', unicode("Số tiền bằng chữ (Amount in word): %s đồng." % (self.DocTienBangChu(self.amount)), "utf-8"),
                              body_format_text_wrap_left_top)

        worksheet.write('B11', unicode("Số tài khoản: (Account number)", "utf-8"), body_format_text_wrap_left)
        worksheet.merge_range('C11:H11', unicode("Danh sách đính kèm", "utf-8"),
                              body_format_red_color_center)

        worksheet.write('B12', unicode("Ngân hàng:   (With bank)", "utf-8"), body_format_text_wrap_left)
        worksheet.merge_range('C12:E12', unicode("Danh sách đính kèm", "utf-8"),
                              body_format_red_color_center)
        worksheet.write('F12', unicode("Tỉnh/TP: (Provinces/City)", "utf-8"), body_format_text_wrap_left)
        worksheet.merge_range('G12:H12', unicode("Đà Nẵng", "utf-8"),
                              body_format_red_color_center)

        worksheet.merge_range('J11:M12', unicode("", "utf-8"),
                              body_format)

        worksheet.merge_range('B13:B14', unicode("Nội dung \n(Details):", "utf-8"),
                              body_format)
        worksheet.merge_range('C13:H14', unicode("Thanh toán lương tháng 11/2018", "utf-8"),
                              body_format)
        worksheet.merge_range('J13:M13', "", header_body_color_bg_tim)
        worksheet.write_rich_string('J13', bold, unicode("Phí Ngân hàng ", "utf-8"), italic,
                                    '(Charges)', header_body_color_bg_tim)
        worksheet.merge_range('J14:L14', unicode("     £ Người chuyển chịu (Sender)", "utf-8"),
                              body_format)

        worksheet.merge_range('B15:E19', "",
                              body_format_text_wrap_mr_top)
        worksheet.write_rich_string('B15', bold, unicode("kế toán trưởng ", "utf-8"),italic,
                                    '\n(Chief accountant)', body_format_text_wrap_mr_top)
        worksheet.merge_range('F15:H19', "",
                              body_format_text_wrap_mr_top)
        worksheet.write_rich_string('F15', bold, unicode("Chủ tài khoản ", "utf-8"), italic,
                                    unicode("(ký và đóng dấu) \n(Holder's signature and stamp)", "utf-8"), body_format_text_wrap_mr_top)
        worksheet.merge_range('J15:L15', unicode("     o Người hưởng chịu (Beneficiary)", "utf-8"),
                              body_format)
        worksheet.merge_range('J16:L16', unicode("Số tiền phí (Amount charge)", "utf-8"),
                              body_format)

        worksheet.merge_range('B20:H20',"", header_body_color_bg_tim)
        worksheet.write_rich_string('B20', bold, unicode("Dành cho Ngân hàng ", "utf-8"), italic,
                                    '(For bank use only)', header_body_color_bg_tim)

        worksheet.merge_range('B21:D26', "",
                              body_format_text_wrap_mr_top)
        worksheet.write_rich_string('B21', bold, unicode("Giao dịch viên ", "utf-8"), italic,
                                    unicode("\n(Teller)", "utf-8"),
                                    body_format_text_wrap_mr_top)
        worksheet.merge_range('E21:H26', "",
                              body_format_text_wrap_mr_top)
        worksheet.write_rich_string('E21', bold, unicode("Người duyệt ", "utf-8"), italic,
                                    unicode("\n(Approver)", "utf-8"),
                                    body_format_text_wrap_mr_top)

        worksheet.write('J21', unicode("Số bút toán:", "utf-8"), body_format_bold)

        worksheet.write('J22', unicode("Nợ TK:", "utf-8"), body_format)
        worksheet.write('J23', unicode("Có TK:", "utf-8"), body_format)
        worksheet.write('J24', unicode("Có TK:", "utf-8"), body_format)

        worksheet.write('L23', unicode("Có TK:", "utf-8"), body_format)
        worksheet.write('L24', unicode("Có TK:", "utf-8"), body_format)

    def create_unc_tc_bank(self, worksheet, workbook):
        tc_bank_logo = os.path.abspath(__file__).split('models')[0] + 'data/tc_bank_logo.jpg'
        bg_red_format = workbook.add_format({
            'bg_color': '#DF0101',
        })

        bg_oran_format = workbook.add_format({
            'bg_color': '#FBD5BB',
        })
        header_body_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'font_color': '#E97941',
            'valign': 'vcenter',
        })

        payment_order_format = workbook.add_format({
            'font_size': '11',
            'align': 'center',
            'valign': 'vcenter',
        })

        body_format = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
        })

        body_format_center = workbook.add_format({
            'font_size': '9',
            'align': 'center',
            'valign': 'vcenter',
        })

        body_format_bold = workbook.add_format({
            'bold': True,
            'font_size': '9',
            'align': 'center',
            'valign': 'top',
            'border': 1,
        })

        body_format_bg_oran = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#FBD5BB',
        })

        body_format_bg_oran_bold = workbook.add_format({
            'bold': True,
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#FBD5BB',
        })

        body_format_bg_brown = workbook.add_format({
            'bold': True,
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': '#929192',
            'font_color': '#FFFFFF',
            'border': 1,
        })

        body_format_have_boder = workbook.add_format({
            'font_size': '9',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
        })

        body_format_text_wrap = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        body_format_number = workbook.add_format({
            'font_size': '9',
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'border': 1,
            'text_wrap': True,
        })

        body_format_bg_black_left = workbook.add_format({
            'font_size': '9',
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': '#000000',
        })

        body_format_bg_black_center = workbook.add_format({
            'font_size': '9',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#000000',
        })

        body_format_bg_E0E1E1_center = workbook.add_format({
            'font_size': '9',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E0E1E1',
        })

        bold = workbook.add_format({
            'bold': True,
            'font_size': '9',
        })
        italic = workbook.add_format({
            'italic': True,
            'font_size': '9',
        })

        normal = workbook.add_format({
            'font_size': '9',
        })

        bold_white = workbook.add_format({
            'bold': True,
            'font_size': '9',
            'font_color': '#FFFFFF',
        })
        italic_white = workbook.add_format({
            'italic': True,
            'font_size': '9',
            'font_color': '#FFFFFF',
        })

        worksheet.set_column('A:A', 19.5)
        worksheet.set_column('B:B', 10.8)
        worksheet.set_column('C:C', 4.5)
        worksheet.set_column('D:D', 12.8)
        worksheet.set_column('E:E', 12.1)
        worksheet.set_column('F:F', 11.2)
        worksheet.set_column('G:G', 1.2)
        worksheet.set_column('H:H', 10.8)
        worksheet.set_column('I:I', 6.5)
        worksheet.set_column('J:J', 25.4)

        worksheet.set_row(1, 25)
        worksheet.set_row(2, 4)
        worksheet.set_row(4, 4)
        worksheet.set_row(5, 4)
        worksheet.set_row(7, 17)
        worksheet.set_row(8, 4)
        worksheet.set_row(9, 25)
        worksheet.set_row(10, 4)
        worksheet.set_row(11, 30)
        worksheet.set_row(12, 4)
        worksheet.set_row(13, 27)
        worksheet.set_row(14, 4)
        worksheet.set_row(15, 27)
        worksheet.set_row(16, 4)
        worksheet.set_row(17, 30)
        worksheet.set_row(18, 4)
        worksheet.set_row(19, 32)
        worksheet.set_row(20, 4)
        worksheet.set_row(21, 27)
        worksheet.set_row(22, 4)
        worksheet.set_row(23, 32)
        worksheet.set_row(24, 4)
        worksheet.set_row(25, 27)
        worksheet.set_row(26, 4)
        worksheet.set_row(27, 30)
        worksheet.set_row(28, 4)
        worksheet.set_row(29, 27)
        worksheet.set_row(31, 40)
        worksheet.set_row(32, 4)
        worksheet.set_row(34, 25)
        worksheet.set_row(35, 40)

        worksheet.insert_image('A1', tc_bank_logo, {})
        worksheet.merge_range('H1:J1', unicode("ỦY NHIỆM CHI", "utf-8"), header_body_color)
        worksheet.merge_range('H2:J2', unicode("Payment order", "utf-8"), payment_order_format)

        worksheet.merge_range('A2:B2', unicode("Liên 1: Ngân hàng giữ (For internal use)", "utf-8"),body_format)

        worksheet.merge_range('A3:J3', unicode("", "utf-8"), bg_red_format)

        worksheet.write('A4', unicode("Ngày(date)", "utf-8"), body_format)
        worksheet.merge_range('H4:J4', unicode("Số bút toán (transaction no.)", "utf-8"), body_format)

        worksheet.merge_range('A5:J5', unicode("", "utf-8"), bg_red_format)

        worksheet.merge_range('A7:A8', unicode("Tên tài khoản \n(Account name)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B7:F8', unicode("CÔNG TY CỔ PHẦN KỸ THUẬT ĐIỆN TUẤN HUY", "utf-8"), body_format_have_boder)
        worksheet.merge_range('H7:J7', unicode("Số tiền giao dịch bằng số/ Amount in Figures", "utf-8"),
                              body_format_bg_brown)
        worksheet.merge_range('H8:J10', self.amount,
                              body_format_number)

        worksheet.write('A10', unicode("Số tài khoản \n(Account No.)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B10:F10', unicode("19122338640012", "utf-8"),
                              body_format_have_boder)

        worksheet.merge_range('H11:J11', unicode("", "utf-8"),
                              bg_oran_format)

        worksheet.write('A12', unicode("Chi nhánh Techcombank\n(Branch)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B12:C12', unicode("Đà Nẵng", "utf-8"),
                              body_format_have_boder)
        worksheet.merge_range('E12:F12', unicode("Đà Nẵng", "utf-8"),
                              body_format_have_boder)
        worksheet.write('D12', unicode("Tỉnh/TP\n(Prov.,City.)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('H12:J12', unicode("Số tiền giao dịch bằng chữ / Amount in words", "utf-8"),
                              body_format_bg_brown)

        worksheet.merge_range('H13:J13', unicode("", "utf-8"),
                              bg_oran_format)

        worksheet.write('A14', unicode("Địa chỉ\n(Address)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B14:F14', unicode("Lô 47, đường số 2, KCN Đà Nẵng, P. An Hải Bắc, Q. Sơn Trà, TP ĐN", "utf-8"),
                              body_format_have_boder)

        worksheet.write('A16', unicode("Người hưởng\n(Beneficiary's name)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B16:F16',
                              unicode(str(self.partner_id.name) or "", "utf-8"),
                              body_format_have_boder)

        worksheet.write('A18', unicode("Số tài khoản\n(Account No.)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B18:F18',str(self.acc_number),
                              body_format_have_boder)

        worksheet.merge_range('H14:J18', unicode("%s đồng." % (self.DocTienBangChu(self.amount)), "utf-8"),
                              body_format_have_boder)
        worksheet.merge_range('H19:J19', unicode("", "utf-8"),
                              bg_oran_format)

        worksheet.write('A20', unicode("CMND/Thẻ CCCD/\nHC (ID card/PP No.)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B20:F20', unicode("", "utf-8"),
                              body_format_have_boder)

        worksheet.write('H20', unicode("Loại tiền\nCurrency", "utf-8"), body_format_bg_oran)
        worksheet.write('I20', unicode("£ VND\n£ EUR", "utf-8"), body_format_bg_oran)
        worksheet.write('J20', unicode("£ USD\n£ Khác ( Other):……..", "utf-8"), body_format_bg_oran)

        worksheet.merge_range('H21:J21', unicode("", "utf-8"),
                              bg_oran_format)

        worksheet.write('A22', unicode("Ngày cấp\n(Date of issue)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B22:C22', unicode("", "utf-8"),
                              body_format_have_boder)
        worksheet.write('D22', unicode("Nơi cấp\n(Place of issue)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('E22:F22', unicode("", "utf-8"),
                              body_format_have_boder)

        worksheet.merge_range('H22:J22', unicode("Phí ngân hàng (Bank's charges)", "utf-8"),
                              body_format_bg_oran_bold)

        worksheet.merge_range('H23:J23', unicode("", "utf-8"),
                              bg_oran_format)

        worksheet.write('A24', unicode("Địa chỉ\n(Address)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B24:F24', unicode("", "utf-8"),
                              body_format_have_boder)
        worksheet.merge_range('H24:J24', unicode("", "utf-8"),
                              body_format_have_boder)

        worksheet.merge_range('H25:J25', unicode("", "utf-8"),
                              bg_oran_format)

        worksheet.write('A26', unicode("Tại Ngân hàng\n(At bank)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B26:F26', unicode("Sacombank", "utf-8"),
                              body_format_have_boder)
        worksheet.merge_range('H26:J26', unicode(" £ Phí trích từ số tiền chuyển / Including", "utf-8"),
                              body_format_bg_oran)

        worksheet.merge_range('H27:J27', unicode("", "utf-8"),
                              bg_oran_format)

        worksheet.write('A28', unicode("Chi nhánh\n(Branch)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('B28:C28', unicode("PGD Nguyễn Văn Linh", "utf-8"),
                              body_format_have_boder)
        worksheet.write('D28', unicode("Tỉnh/TP\n(Prov.,City.)", "utf-8"), body_format_text_wrap)
        worksheet.merge_range('E28:F28', unicode("Đà Nẵng", "utf-8"),
                              body_format_have_boder)
        worksheet.merge_range('H28:J28', unicode(" £ Phí  nộp thêm / Excluding", "utf-8"),
                              body_format_bg_oran)

        worksheet.merge_range('H29:J29', unicode("", "utf-8"),
                              bg_oran_format)

        worksheet.merge_range('A30:J30', unicode("", "utf-8"),
                              body_format_bg_black_left)
        worksheet.write_rich_string('A30', bold_white, unicode("Nội dung / ", "utf-8"), italic_white,
                                    unicode("(Details)", "utf-8"), body_format_bg_black_left)

        note = ""
        for line in self.line_ids:
            note += line.name +", "
        worksheet.merge_range('A31:J32', unicode(str(note), "utf-8"),
                              body_format_bold)

        worksheet.merge_range('A34:E34', unicode("", "utf-8"),
                              body_format_bg_black_center)
        worksheet.write_rich_string('A34', bold_white, unicode("Đơn vị chuyển / ", "utf-8"), italic_white,
                                    unicode("Payer", "utf-8"), body_format_bg_black_center)
        worksheet.merge_range('F34:G34', unicode("", "utf-8"),
                              body_format_bg_black_center)
        worksheet.merge_range('H34:J34', unicode("", "utf-8"),
                              body_format_bg_black_center)
        worksheet.write_rich_string('H34', bold_white, unicode("Ngân hàng chuyển / ", "utf-8"), italic_white,
                                    unicode("Techcombank", "utf-8"), body_format_bg_black_center)

        worksheet.merge_range('A35:E35', unicode("", "utf-8"),
                              body_format)
        worksheet.write_rich_string('A35', bold, unicode("Ghi sổ ngày ", "utf-8"), italic,
                                    unicode("(Settlement date)", "utf-8"),normal,"…./……/………..", body_format_center)
        worksheet.merge_range('F35:J35', unicode("", "utf-8"),
                              body_format)
        worksheet.write_rich_string('F35', bold, unicode("Ghi sổ ngày ", "utf-8"), italic,
                                    unicode("(Settlement date)", "utf-8"),normal, "…./……/………..", body_format_center)

        worksheet.merge_range('A36:B36', unicode("", "utf-8"),
                              body_format_bg_E0E1E1_center)
        worksheet.write_rich_string('A36', bold, unicode("Kế toán trưởng/ ", "utf-8"), italic,
                                    unicode("Chief Accountant", "utf-8"),normal, "\n(Ký, ghi rõ họ tên / Sign , Full name)", body_format_bg_E0E1E1_center)
        worksheet.merge_range('C36:E36', unicode("", "utf-8"),
                              body_format_bg_E0E1E1_center)
        worksheet.write_rich_string('C36', bold, unicode("CTK/NĐDHP của CTK/ ", "utf-8"), italic,
                                    unicode("Representative", "utf-8"), normal,"\n( Ký, ghi rõ họ tên , đóng dấu / Signature, full \nname and seal)",
                                    body_format_bg_E0E1E1_center)
        worksheet.merge_range('F36:H36', unicode("", "utf-8"),
                              body_format_bg_E0E1E1_center)
        worksheet.write_rich_string('F36', bold, unicode("Kế toán/ ", "utf-8"), italic,
                                    unicode("Accountant", "utf-8"),body_format_bg_E0E1E1_center)
        worksheet.merge_range('I36:J36', unicode("", "utf-8"),
                              body_format_bg_E0E1E1_center)
        worksheet.write_rich_string('I36', bold, unicode("Kiểm soát viên/ ", "utf-8"), italic,
                                    unicode("Supervisor", "utf-8"), body_format_bg_E0E1E1_center)

        for i in range(36,42):
            for j in range(0,10):
                worksheet.write(i,j, "", body_format_bg_E0E1E1_center)

        worksheet.merge_range('A43:F43', unicode("Dịch vụ chăm sóc khách hàng 24/7 (miễn phí); 1800588822     Email: call_center@techcombank.com.vn", "utf-8"),
                              body_format_bg_E0E1E1_center)
        worksheet.write("G43", "", body_format_bg_E0E1E1_center)
        worksheet.write("H43", "", body_format_bg_E0E1E1_center)
        worksheet.write("I43", "", body_format_bg_E0E1E1_center)
        worksheet.write("J43", "", body_format_bg_E0E1E1_center)





