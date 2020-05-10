# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class import_product_template(models.TransientModel):
    _name = 'import.tts_journal_entry.nhatkychung'

    data_import = fields.Binary()

    def import_data_excel(self):
        try:
            data = base64.b64decode(self.data_import)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)

            for row_no in range(sheet.nrows):

                if row_no > 0:
                    row = (
                    map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))

                    date = row[0].strip()
                    date = datetime.strptime(date, "%d/%m/%Y").strftime(DEFAULT_SERVER_DATE_FORMAT)
                    dien_giai = row[1].strip()
                    try:
                        tai_khoan_no_code = str(int(float(row[2].strip())))
                    except:
                        tai_khoan_no_code = row[2].strip()
                    tai_khoan_no = self.env['account.account'].search([('code','=',tai_khoan_no_code)],limit=1)
                    if not tai_khoan_no:
                        raise UserError('Không tìm thấy tài khoản với mã code %s'% (tai_khoan_no_code))

                    try:
                        tai_khoan_co_code = str(int(float(row[3].strip())))
                    except:
                        tai_khoan_co_code = row[3].strip()
                    tai_khoan_co = self.env['account.account'].search([('code', '=', tai_khoan_co_code)], limit=1)
                    if not tai_khoan_co:
                        raise UserError('Không tìm thấy tài khoản với mã code %s' % (tai_khoan_no_code))

                    group_level_1_name = row[4].strip()
                    group_level_1 = self.env['journal.entry.category'].search([('name','=',group_level_1_name),('level','=','level_1')],limit=1)
                    if not group_level_1:
                        group_level_1 = self.env['journal.entry.category'].create({
                            'name' : group_level_1_name,
                            'level' : 'level_1',
                        })

                    group_level_2_name = row[5].strip()
                    group_level_2 = self.env['journal.entry.category'].search(
                        [('name', '=', group_level_2_name), ('level', '=', 'level_2')], limit=1)
                    if not group_level_2:
                        group_level_2 = self.env['journal.entry.category'].create({
                            'name': group_level_2_name,
                            'level': 'level_2',
                        })

                    group_level_3_name = row[6].strip()
                    group_level_3 = self.env['journal.entry.category'].search(
                        [('name', '=', group_level_3_name), ('level', '=', 'level_3')], limit=1)
                    if not group_level_3:
                        group_level_3 = self.env['journal.entry.category'].create({
                            'name': group_level_3_name,
                            'level': 'level_3',
                        })

                    ma_doi_tuong_co = row[7].strip()
                    ma_doi_tuong_co_id = self.env['res.partner'].search([('name','=',ma_doi_tuong_co)],limit=1)
                    if not ma_doi_tuong_co_id:
                        ma_doi_tuong_co_id = self.env['res.partner'].create({
                            'name' : ma_doi_tuong_co
                        })
                    ma_doi_tuong_no = row[8].strip()
                    ma_doi_tuong_no_id = self.env['res.partner'].search([('name', '=', ma_doi_tuong_no)], limit=1)
                    if not ma_doi_tuong_no_id:
                        ma_doi_tuong_no_id = self.env['res.partner'].create({
                            'name': ma_doi_tuong_no
                        })

                    so_tien = float(row[9].strip())

                    nkc_data = {
                        'date' : date,
                        'dien_giai' : dien_giai,
                        'tai_khoan_no' : tai_khoan_no.id,
                        'tai_khoan_co' : tai_khoan_co.id,
                        'group_level_1' : group_level_1.id,
                        'group_level_2': group_level_2.id,
                        'group_level_3': group_level_3.id,
                        'ma_doi_tuong_co' : ma_doi_tuong_co_id.id,
                        'ma_doi_tuong_no' : ma_doi_tuong_no_id.id,
                        'so_tien' : so_tien,
                    }

                    nkc_id = self.env['tts_journal_entry.nhatkychung'].create(nkc_data)

        except:
            raise UserError('Lỗi format file nhập')

    def export_data_excel(self):
        download_url = '/web/content/' + str(self.env.ref('tts_journal_entry.attachment_export_nkc').id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }