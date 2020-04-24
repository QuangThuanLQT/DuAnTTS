# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import StringIO
import xlsxwriter


class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'

    account_asset_code     = fields.Char(string='Mã tài sản')
    depreciation_total_qty = fields.Float(string="Số kỳ KH", compute="get_depreciation")
    depreciation_qty       = fields.Float(string="Số kỳ đã KH", compute="get_depreciation")
    depreciation_amount    = fields.Float(string="Mức KH",compute="get_depreciation")
    depreciation_date_near = fields.Datetime(string="Ngày KH gần nhất",compute="get_depreciation")
    remain_depreciation    = fields.Float("Số kỳ sử dụng còn lại (tháng)")
    depreciation_month     = fields.Float("Giá trị KH tháng")
    account_ids              = fields.Many2many('account.account','tai_khoan_nguyen_gia_rel','asset_id','account_id',string='TK nguyên giá',compute="get_account")
    depreciation_account_ids = fields.Many2many('account.account','tai_khoan_khau_hao_rel','asset_id','account_id',string='TK khấu hao',compute="get_account")
    use_state              = fields.Selection([('using','Đang sử dụng'),('not_yet','Chưa sử dụng')],string='Tình trạng sử dụng',default='using')
    quality_state          = fields.Selection([('good','Chất lượng tốt'),('bad','Chất lượng kém')],string='Chất lượng hiện thời',default='good')
    origin_asset           = fields.Selection([('new','Mua mới'),('not','Chưa mua')],string='Nguồn gốc hình thành')

    @api.multi
    def get_account(self):
        for record in self:
            if record.depreciation_line_ids:
                record.account_ids = record.depreciation_line_ids.mapped('move_id.line_ids').filtered(lambda rec:rec.debit > rec.credit).mapped('account_id')
                record.depreciation_account_ids = record.depreciation_line_ids.mapped('move_id.line_ids').filtered(lambda rec:rec.credit > rec.debit).mapped('account_id')


    @api.model
    def create(self, vals):
        res = super(account_asset_asset, self).create(vals)
        res.account_asset_code = self.env['ir.sequence'].next_by_code('account.asset.asset')
        return res

    @api.multi
    def get_depreciation(self):
        for rec in self:
            if rec.depreciation_line_ids.filtered(lambda d: d.move_posted_check):
                depreciation_true = rec.depreciation_line_ids.filtered(lambda d: d.move_posted_check)
                rec.depreciation_qty = len(depreciation_true)
                rec.depreciation_total_qty = len(rec.depreciation_line_ids)
                rec.remain_depreciation = rec.depreciation_total_qty - rec.depreciation_qty
                depreciation_dates = sorted(depreciation_true.mapped("depreciation_date"), reverse=True)
                rec.depreciation_date_near = depreciation_dates[0]
                if rec.depreciation_line_ids.filtered(lambda d: d.move_posted_check == False):
                    rec.depreciation_amount = rec.depreciation_line_ids[len(depreciation_true)].amount
                else:
                    rec.depreciation_amount = 0

    @api.model
    def print_account_asset_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        line_ids = self.env['account.asset.asset'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Tổng hợp tài sản')
        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0.##')
        worksheet.set_column('A:A', 80)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)

        worksheet.set_column('J:J', 10)
        summary_header = ['Tên tài sản', 'Mã tài sản', 'Chuyên mục',
            'Ngày tháng', 'Số kỳ KH',
            'Mức KH', 'Ngày KH gần nhất', 'Giá trị gộp', 'Giá trị còn lại', 'Trạng thái']
        row = 0
        [worksheet.write(row, header_cell, unicode(str(summary_header[header_cell]), "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        for line in line_ids:
            row +=1
            if line.date:
                date = datetime.strptime(line.date, "%Y-%m-%d").date().strftime("%d/%m/%Y")
            if line.depreciation_date_near:
                depreciation_date_near = datetime.strptime(line.depreciation_date_near, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")
            worksheet.write(row, 0, line.name, text_style)
            worksheet.write(row, 1, line.account_asset_code, text_style)
            worksheet.write(row, 2, line.category_id.name, text_style)
            worksheet.write(row, 3, date, text_style)
            worksheet.write(row, 4, line.depreciation_qty, text_style)
            worksheet.write(row, 5, line.depreciation_amount, body_bold_color_number)
            worksheet.write(row, 6, depreciation_date_near, text_style)
            worksheet.write(row, 7, line.value, body_bold_color_number)
            worksheet.write(row, 8, line.value_residual, body_bold_color_number)
            worksheet.write(row, 9, line.state, text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def action_wizard_run_account_asset(self):
        action = self.env.ref('cptuanhuy_accounting.action_wizard_account_asset').read()[0]
        action['context'] = self._context
        return action


class account_asset_asset_wizard(models.TransientModel):
    _name = 'account.asset.asset.wizard'

    start_date = fields.Date(String='Từ Ngày')
    end_date = fields.Date(String='Đến Ngày')
    depreciation_line_ids = fields.Many2many('account.asset.depreciation.line')

    @api.multi
    def search_line(self):
        active_ids = self._context.get('active_ids', [])
        line_ids = self.env['account.asset.depreciation.line'].search(
            [('asset_id', 'in', active_ids), ('depreciation_date', '>=', self.start_date),
             ('depreciation_date', '<=', self.end_date), ('asset_id.state', '!=', 'close')])
        self.depreciation_line_ids = line_ids
        return {"type": "ir.actions.do_nothing"}

    @api.multi
    def action_confirm(self):
        for line in self.depreciation_line_ids:
            if line.asset_id == 'draft':
                line.asset_id.validate()
                if not line.move_check:
                    line.create_move()
                    line.move_id.post()
                else:
                    line.move_id.post()
            else:
                if not line.move_check:
                    line.create_move()
                    line.move_id.post()
                else:
                    line.move_id.post()

        return
