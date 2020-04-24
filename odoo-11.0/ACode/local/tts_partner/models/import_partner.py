# -*- coding: utf-8 -*-

from odoo import models, fields, api
import StringIO
import xlsxwriter
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook
from odoo.exceptions import UserError, ValidationError


class import_res_partner(models.Model):
    _name = 'import.res.partner'

    data_import = fields.Binary()


    def import_csv(self):

        data = base64.b64decode(self.data_import)
        wb = open_workbook(file_contents=data)
        sheet = wb.sheet_by_index(0)
        # line_ids = self.planning_ids.browse([])
        for row_no in range(sheet.nrows):
            if row_no > 0:
                row = (map(lambda row: isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value),
                           sheet.row(row_no)))
                if not row[0]:
                    continue
                else:
                    partner_data = {
                        'name': row[2],
                        'phone': row[4],
                        'mobile': row[5],
                        'street': row[6],
                        'website': row[18],
                        'email': row[19],
                        'customer': True,
                        'sale_type': 'allow',
                        'delivery_method': row[11],
                    }
                    if row[9]:
                        city_id = self.env['feosco.city'].search([('name', 'like', row[9])], limit=1)
                        if city_id:
                            partner_data['feosco_city_id'] = city_id.id
                        else:
                            print ("Tinh '%s' row : %s" % (row[9], row_no))
                        if row[8]:
                            district_id = self.env['feosco.district'].search([('name', 'like', row[8]), ('city_id', '=', city_id.id)], limit=1)
                            if district_id:
                                partner_data['feosco_district_id'] = district_id.id
                            else:
                                print ("Quan '%s' row : %s" % (row[8], row_no))
                            if row[7]:
                                ward_id = self.env['feosco.ward'].search(
                                    [('name', 'like', row[7]), ('district_id', '=', district_id.id)], limit=1)
                                if district_id:
                                    partner_data['feosco_ward_id'] = ward_id.id
                                else:
                                    print ("Xa '%s' row : %s" % (row[7], row_no))
                    if row[12]:
                        payment_method = self.env['account.journal'].search([('name', '=', row[12]), ('type', 'in', ['cash', 'bank'])], limit=1)
                        if payment_method:
                            partner_data['payment_method'] = payment_method.id
                    if row[10]:
                        user_id = self.env['res.users'].search([('name', '=', row[10])], limit=1)
                        if user_id:
                            partner_data['user_id'] = user_id.id
                    if row[20]:
                        group_kh1_id = self.env['partner.group.hk1'].search([('name', '=', row[20])], limit=1)
                        if not group_kh1_id:
                            group_kh1_id = self.env['partner.group.hk1'].create({'name': row[20]})
                        partner_data['group_kh1_id'] = group_kh1_id.id
                    if row[21]:
                        group_kh2_id = self.env['partner.group.hk2'].search([('name', '=', row[21])], limit=1)
                        if not group_kh2_id:
                            group_kh2_id = self.env['partner.group.hk2'].create({'name': row[21]})
                        partner_data['group_kh2_id'] = group_kh2_id.id
                    if row[17]:
                        partner_data['feosco_birthday'] = row[17]
                    partner_id = self.env['res.partner'].create(partner_data)
                    partner_id.write({
                        'create_date': datetime.strptime(row[3], "%d/%m/%Y %H:%M"),
                        'ref': row[0]
                    })
                    partner_id.onchange_get_delivery_scope()
                    print ('Done %s' % row_no)


    def import_user(self):
        data = base64.b64decode(self.data_import)
        wb = open_workbook(file_contents=data)
        sheet = wb.sheet_by_index(0)
        # line_ids = self.planning_ids.browse([])
        for row_no in range(sheet.nrows):
            if row_no > 0:
                row = (map(lambda row: isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value),
                           sheet.row(row_no)))
                if not row[1]:
                    continue
                else:
                    if row[11]:
                        user_id = self.env['res.users'].search([('name', '=', row[11])], limit=1)
                        if not user_id:
                            user_data = {
                                'name': row[11],
                                'email': 'tts%s' % row_no,
                                'login': 'tts%s' % row_no,
                            }
                            user_id = self.env['res.users'].create(user_data)
                        partner_id = self.env['res.partner'].search([('phone', '=', row[3])])
                        if partner_id:
                            partner_id.user_id = user_id

