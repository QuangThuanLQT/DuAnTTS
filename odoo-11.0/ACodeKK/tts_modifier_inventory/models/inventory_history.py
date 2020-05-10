# -*- coding: utf-8 -*-

from odoo import models, fields, api
import StringIO
import xlsxwriter
from datetime import datetime
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
import base64

class inventory_history(models.Model):
    _name = 'inventory.history'

    name = fields.Many2one('sale.order', readonly=1,string='Đơn hàng')
    thoi_gian_tao_pick = fields.Datetime(string='Thời gian khởi tạo pick')
    user_tao_pick = fields.Many2one('res.users', )

    thoi_gian_bat_dau_pick = fields.Datetime(string='Thời gian bắt đầu pick')
    user_bat_dau_pick = fields.Many2one('res.users', )

    thoi_gian_tao_pack = fields.Datetime(string='Thời gian khởi tạo pack')
    user_tao_pack = fields.Many2one('res.users', )

    thoi_gian_tao_delivery = fields.Datetime(string='Thời gian khởi tạo delivery')
    user_tao_delivery = fields.Many2one('res.users', )

    thoi_gian_bat_dau_delivery = fields.Datetime(string='Thời gian bắt đầu giao hàng')
    user_bat_dau_delivery = fields.Many2one('res.users', )

    thoi_gian_hoan_tat_delivery = fields.Datetime(string='Thời gian hoàn tất giao hàng')
    user_hoan_tat_delivery = fields.Many2one('res.users', )

    inventory_history_id = fields.Many2one('inventory.history')

    def get_str_utc_time(self,date):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        date = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
        return pytz.utc.localize(date).astimezone(user_tz).strftime('%H:%M %d/%m/%Y')

    @api.multi
    def print_inventory_history(self):
        ids = self.env.context.get('active_ids', [])
        history_ids = self.browse(ids)

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Lịch sử công đoạn kho')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:D', 20)
        worksheet.set_column('E:G', 25)

        summary_header = ['Đơn hàng', 'Thời gian khởi tạo pick', 'Thời gian bắt đầu pick', 'Thời gian khởi tạo pack', 'Thời gian khởi tạo delivery',
                          'Thời gian bắt đầu giao hàng', 'Thời gian hoàn tất giao hàng']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for history_id in history_ids:
            row += 1
            worksheet.write(row, 0, history_id.name.name, text_style)
            worksheet.write(row, 1, self.get_str_utc_time(history_id.thoi_gian_tao_pick) if history_id.thoi_gian_tao_pick else '', text_style)
            worksheet.write(row, 2, self.get_str_utc_time(history_id.thoi_gian_bat_dau_pick) if history_id.thoi_gian_bat_dau_pick else '', text_style)
            worksheet.write(row, 3, self.get_str_utc_time(history_id.thoi_gian_tao_pack) if history_id.thoi_gian_tao_pack else '', text_style)
            worksheet.write(row, 4, self.get_str_utc_time(history_id.thoi_gian_tao_delivery) if history_id.thoi_gian_tao_delivery else '', text_style)
            worksheet.write(row, 5, self.get_str_utc_time(history_id.thoi_gian_bat_dau_delivery) if history_id.thoi_gian_bat_dau_delivery else '', text_style)
            worksheet.write(row, 6, self.get_str_utc_time(history_id.thoi_gian_hoan_tat_delivery) if history_id.thoi_gian_hoan_tat_delivery else '', text_style)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'Lịch sử công đoạn kho.xlsx',
            'datas_fname': 'Lịch sử công đoạn kho.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }



