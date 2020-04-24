# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import base64
import StringIO
import xlsxwriter
from calendar import monthrange


class tts_journal_entry_report(models.TransientModel):
    _name = 'journal.entry.report'

    def get_years(self):
        year_list = []
        for i in range(2010, 2031):
            year_list.append((i, str(i)))
        return year_list

    # Inside the model
    month_start = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                                    (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                                    (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
                                   string='Month', required=True)

    month_stop = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                                   (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                                   (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
                                  string='Month', required=10)
    year = fields.Selection(get_years, string='Year', required=True)

    def get_name(self, id):
        name = ''
        id = self.env['journal.entry.category'].browse(id)
        if id and id.name:
            name = id.name
        return name

    def get_data(self, start_month, end_month, year):
        date_start = monthrange(year, start_month)
        start_date = datetime(year, start_month, date_start[0]).strftime(DEFAULT_SERVER_DATE_FORMAT)

        date_end = monthrange(year, end_month)
        end_date = datetime(year, end_month, date_end[1]).strftime(DEFAULT_SERVER_DATE_FORMAT)

        list_level_1 = []
        query = """SELECT DISTINCT group_level_1 FROM account_move_line WHERE date >= '%s' AND date <= '%s' AND group_level_1 is not null;""" % (
            start_date, end_date)
        self.env.cr.execute(query)
        group_level_1_data = self.env.cr.fetchall()
        if group_level_1_data and group_level_1_data[0]:
            for line in group_level_1_data:
                list_level_1.append(line[0])

        result = []
        for level_1 in list_level_1:
            data = []
            list_level_2 = []
            query_lv2_ids = """SELECT DISTINCT group_level_2 FROM account_move_line WHERE date >= '%s' AND date <= '%s'  AND group_level_1 = %s;""" % (
                start_date, end_date, level_1)
            self.env.cr.execute(query_lv2_ids)
            group_level_2_data = self.env.cr.fetchall()
            if group_level_2_data[0] and group_level_2_data[0][0]:
                for line in group_level_2_data:
                    list_level_2.append(line[0])
            for month in range(start_month, end_month + 1, 1):
                total_level_1 = 0
                level_2_data = []
                date_month = monthrange(year, month)
                start_date_month = datetime(year, month, 1).strftime(DEFAULT_SERVER_DATE_FORMAT)
                end_date_month = datetime(year, month, date_month[1]).strftime(DEFAULT_SERVER_DATE_FORMAT)
                query = """SELECT SUM(debit + credit) as total FROM account_move_line WHERE date >= '%s' AND date <= '%s' AND group_level_1 = %s;""" % (
                    start_date_month, end_date_month, level_1)
                self.env.cr.execute(query)
                group_level_1_value = self.env.cr.fetchall()
                if group_level_1_value[0] and group_level_1_value[0][0]:
                    total_level_1 = group_level_1_value[0][0]

                for level_2 in list_level_2:
                    total_level_2 = 0
                    level_3_data = []
                    list_level_3 = []

                    query_level_2_value = """SELECT SUM(debit + credit) FROM account_move_line WHERE date >= '%s' AND date <= '%s' AND group_level_2 = %s AND group_level_1 = %s;""" % (
                        start_date_month, end_date_month, level_2, level_1)
                    self.env.cr.execute(query_level_2_value)
                    group_level_2_value = self.env.cr.fetchall()
                    if group_level_2_value[0] and group_level_2_value[0][0]:
                        total_level_2 = group_level_2_value[0][0]

                    query_lv3_ids = """SELECT DISTINCT group_level_3 FROM account_move_line WHERE date >= '%s' AND date <= '%s'  AND group_level_2 = %s;""" % (
                        start_date, end_date, level_2)
                    self.env.cr.execute(query_lv3_ids)
                    group_level_3_data = self.env.cr.fetchall()
                    if group_level_3_data[0] and group_level_3_data[0][0]:
                        for line in group_level_3_data:
                            list_level_3.append(line[0])

                    for level_3 in list_level_3:
                        total_level_3 = 0
                        query_level_3_value = """SELECT SUM(debit + credit) FROM account_move_line WHERE date >= '%s' AND date <= '%s' AND group_level_3 = %s and group_level_2 = %s AND group_level_1 = %s;""" % (
                            start_date_month, end_date_month, level_3, level_2, level_1)
                        self.env.cr.execute(query_level_3_value)
                        group_level_3_value = self.env.cr.fetchall()
                        if group_level_3_value[0] and group_level_3_value[0][0]:
                            total_level_3 = group_level_3_value[0][0]
                        data3 = {
                            'level_3': level_3,
                            'total': total_level_3
                        }
                        level_3_data.append(data3)

                    data_lv2 = {
                        'level_2': level_2,
                        'value': total_level_2,
                        'level_3_data': level_3_data
                    }
                    level_2_data.append(data_lv2)

                data_lv1 = {
                    'level_1': level_1,
                    'total_level_1': total_level_1,
                    'level_2_data': level_2_data
                }
                data.append(data_lv1)
            data_total_lv1 = {
                'level_1': level_1,
                'data': data
            }
            result.append(data_total_lv1)
        return result

    def export_data_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data = self.get_data(self.month_start, self.month_stop, int(self.year))
        worksheet = workbook.add_worksheet('BaoCao')

        worksheet.set_column('A:A', 2)
        worksheet.set_column('B:B', 2)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 12)
        worksheet.set_column('H:H', 12)
        worksheet.set_column('I:I', 12)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 12)
        worksheet.set_column('L:L', 12)
        worksheet.set_column('M:M', 12)
        worksheet.set_column('N:N', 12)
        worksheet.set_column('O:O', 12)

        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '11',
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': 'cce0ff',
            'border': 1,
        })
        lv2_text = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        lv1_text = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        money_lv1 = workbook.add_format({
            'num_format': '#,##0',
            'bold': True,
        })
        money_lv2 = workbook.add_format({
            'num_format': '#,##0',
            'bold': False,
        })
        header = ['Thang %s'%i  for i in range(self.month_start, self.month_stop + 1, 1)]
        row = 3
        worksheet.merge_range('A4:C4', unicode("", "utf-8"), header_bold_color)

        [worksheet.write(row, header_cell + 3, unicode(header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(header)) if header[header_cell]]
        row = 4
        col = 0
        for level_1 in data:
            col1 = col
            for month in level_1.get('data'):
                row1 = row
                worksheet.write(row1, col1, self.get_name(month.get('level_1')), lv1_text)
                row1 += 1
                for level2 in month.get('level_2_data'):
                    col2 = col + 1
                    worksheet.write(row1, col2, self.get_name(level2.get('level_2')), lv1_text)
                    row1 += 1
                    for level3 in level2.get('level_3_data'):
                        col3 = col + 2
                        worksheet.write(row1, col3, self.get_name(level3.get('level_3')), lv2_text)
                        row1 += 1
                col1 += 1
                break
            row = row1
            row += 1


        row = 4
        col = 3
        for level_1 in data:
            col1 = col
            for month in level_1.get('data'):
                row1 = row
                worksheet.write(row1, col1, month.get('total_level_1') if month.get('total_level_1') !=0 else '', money_lv1)
                row1 += 1
                for level2 in month.get('level_2_data'):
                    worksheet.write(row1, col1, level2.get('value')  if level2.get('value') !=0 else '', money_lv1)
                    row1 += 1
                    for level3 in level2.get('level_3_data'):
                        worksheet.write(row1, col1, level3.get('total')  if level3.get('total') !=0 else '', money_lv2)
                        row1 += 1
                col1 += 1
            row = row1
            row += 1
            True
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'BaoCao.xlsx', 'datas_fname': 'BaoCao.xlsx', 'datas': result})
        self.attachment_id = attachment_id
        if 'get_attachment' in self._context:
            return True
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}
