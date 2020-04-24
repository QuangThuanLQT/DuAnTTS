# -*- coding: utf-8 -*-

from odoo import models, fields, api
import StringIO
import xlsxwriter
import base64
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime

class tts_journal_entry(models.Model):
    _name = 'tts_journal_entry.nhatkychung'

    date = fields.Date()
    dien_giai = fields.Char()
    tai_khoan_no = fields.Many2one('account.account', ondelete='set null', index=True)
    tai_khoan_co = fields.Many2one('account.account', ondelete='set null', index=True)
    ma_doi_tuong_co = fields.Many2one('res.partner')
    ma_doi_tuong_no = fields.Many2one('res.partner')
    so_tien = fields.Float()
    trang_thai = fields.Selection([('da_vao_so', 'Đã vào sổ'), ('chua_vao_so', 'Chưa vào sổ')], default='chua_vao_so', readonly=True)
    account_move_id = fields.Many2one('account.move', ondelete='set null', index=True, invisible=True)
    group_level_1 = fields.Many2one('journal.entry.category', domain=[('level', '=', 'level_1')],
                                    context="{'default_level' : 'level_1'}", string='Nhóm tài khoản 1')
    group_level_2 = fields.Many2one('journal.entry.category', domain=[('level', '=', 'level_2')],
                                    context="{'default_level' : 'level_2'}", string='Nhóm tài khoản 2')
    group_level_3 = fields.Many2one('journal.entry.category', domain=[('level', '=', 'level_3')],
                                    context="{'default_level' : 'level_3'}", string='Nhóm tài khoản 3')
    state = fields.Selection([('draft', 'Draft'),
         ('done', 'Posted')], string='Trạng thái', default='draft')
    @api.model
    def print_nkc_excel(self,response):
        nkc_ids = self.env['tts_journal_entry.nhatkychung'].search([])
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Nhật ký chung')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)

        summary_header = ['Ngày ghi sổ', 'Diễn giải', 'Tài khoản nợ', 'Tài khoản có', 'Mã đối tượng nợ', 'Mã đối tượng có',  'Số tiền',
                          'Trạng thái', 'TK nợ nhóm 1', 'TK nợ nhóm 2', 'TK nợ nhóm 3', 'TK có nhóm 1', 'TK có nhóm 2', 'TK có nhóm 3']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for nkc_id in nkc_ids:
            row += 1
            trang_thai = dict(self.env['tts_journal_entry.nhatkychung'].fields_get(allfields=['trang_thai'])['trang_thai']['selection'])
            worksheet.write(row, 0, datetime.strptime(nkc_id.date, "%Y-%m-%d").strftime("%d/%m/%Y") if nkc_id.date else '', text_style)
            worksheet.write(row, 1, nkc_id.dien_giai, text_style)
            worksheet.write(row, 2, nkc_id.tai_khoan_no.display_name, text_style)
            worksheet.write(row, 3, nkc_id.tai_khoan_co.display_name, text_style)
            worksheet.write(row, 4, nkc_id.ma_doi_tuong_no.name, text_style)
            worksheet.write(row, 5, nkc_id.ma_doi_tuong_co.name, text_style)
            worksheet.write(row, 6, nkc_id.so_tien, body_bold_color_number)
            worksheet.write(row, 7, trang_thai.get(nkc_id.trang_thai), text_style)
            worksheet.write(row, 8, '', text_style)
            worksheet.write(row, 9, '', text_style)
            worksheet.write(row, 10, '', text_style)
            worksheet.write(row, 11, '', text_style)
            worksheet.write(row, 12, '', text_style)
            worksheet.write(row, 13, '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.multi
    def action_confirm(self):
        for rec in self:
            account_journal_id = self.env['account.journal'].search([('name','=','Miscellaneous Operations')],limit=1)
            account_move_obj = self.env['account.move'].with_context({'not_base_account' : True})
            account_move_id = account_move_obj.create({
                'journal_id': account_journal_id.id,
                'date': rec.date,
                'line_ids': [(0, 0, {
                    'account_id': rec.tai_khoan_no.id,
                    'name': rec.dien_giai,
                    'debit': rec.so_tien,
                    'group_level_1': rec.group_level_1.id,
                    'group_level_2': rec.group_level_2.id,
                    'group_level_3': rec.group_level_3.id,
                    'partner_id' : rec.ma_doi_tuong_no.id,
                }), (0, 0, {
                    'account_id': rec.tai_khoan_co.id,
                    'name': rec.dien_giai,
                    'credit': rec.so_tien,
                    'group_level_1': rec.group_level_1.id,
                    'group_level_2': rec.group_level_2.id,
                    'group_level_3': rec.group_level_3.id,
                    'partner_id': rec.ma_doi_tuong_co.id,
                })]
            })

            account_move_id.post()

            rec.account_move_id = account_move_id
            rec.trang_thai = 'da_vao_so'

        # create({
        #     'line_ids' : [(0,0,{
        #         'account_id' : self.tai_khoan_no.id,
        #     }),(0,0,{
        #         'account_id' : self.tai_khoan_co.id,
        #     })]
        # })

    @api.model
    def create(self, val):
        rec = super(tts_journal_entry, self).create(val)
        if rec.state and rec.state == 'done':
            rec.action_confirm()
        return rec
