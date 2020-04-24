# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import fields, models, api
import os
import json
import xlrd

class feosco_master_data(models.Model):
    _name = "feosco.master.data"
    _description = "Master data for all feosco modules"

    name = fields.Char('Name', size=256)
    code = fields.Char('Code', size=256)
    type = fields.Char('Type', size=256)

    sql_constraints = [
        ('name', 'unique(name)', 'The key must be unique'),
        ('code', 'unique(code)', 'The code must be unique')
    ]

    @api.model
    def update_vn_location(self):
        dir_path = os.path.abspath(__file__).split('model')[0]
        file_name = '%s/data/Danh sách cấp huyện kèm theo phường xã __30_05_2019.xls' % (dir_path)

        workbook = xlrd.open_workbook(file_name)
        worksheet = workbook.sheet_by_index(0)

        num_rows = worksheet.nrows - 1
        curr_row = 0

        while curr_row < num_rows:
            curr_row += 1
            row = worksheet.row(curr_row)
            pro_code = row[1].value.strip()
            pro_name = row[0].value.strip()
            if pro_code:
                city_id = self.env['feosco.city'].search([('name', '=', pro_name)])
                if city_id:
                    if city_id.code != pro_code:
                        city_id.code = pro_code
                        print "----- Update TP : %s" % (pro_name)
                else:
                    city_id = self.env['feosco.city'].create({
                        'name': pro_name,
                        'code': pro_code,
                        'country_id': self.env.ref('base.vn').id
                    })
                    print "----- Tao TP : %s" % (pro_name)
                distr_code = row[3].value.strip()
                distr_name = row[2].value.strip()
                if distr_code:
                    distr_id = self.env['feosco.district'].search(
                        [('name', '=', distr_name), ('city_id', '=', city_id.id)])
                    if distr_id:
                        if distr_id.code != distr_code:
                            distr_id.code = distr_code
                            print "+++ Update huyen : %s" % (distr_name)
                    else:
                        distr_id = self.env['feosco.district'].create({
                            'name': distr_name,
                            'code': distr_code,
                            'city_id': city_id.id
                        })
                        print "+++ Tao huyen : %s" % (distr_name)
                    ward_code = row[5].value.strip()
                    ward_name = row[4].value.strip()
                    ward_id = self.env['feosco.ward'].search(
                        [('name', '=', ward_name), ('district_id', '=', distr_id.id)])
                    if ward_id:
                        if ward_id.code != ward_code:
                            ward_id.code = ward_code
                            print "Update xa : %s" % (ward_name)
                    else:
                        ward_id = self.env['feosco.ward'].create({
                            'name': ward_name,
                            'code': ward_code,
                            'district_id': distr_id.id
                        })
                        print "Tao xa : %s" % (ward_name)




        # @api.model
    # def update_vn_location(self):
    #     dir_path = os.path.abspath(__file__).split('model')[0]
    #
    #     with open('%s/vietnam-subdivisions/provinces.json' % (dir_path)) as provinces:
    #         provinces = json.load(provinces)
    #         for provin in provinces:
    #             pro_code = provin.get('LocationID',False).strip()
    #             pro_name = provin.get('LocationName',False).strip()
    #             if pro_code:
    #                 city_id = self.env['feosco.city'].search([('name','=',pro_name)])
    #                 if city_id:
    #                     city_id.code = pro_code
    #                     print "----- Update TP : %s" % (pro_name)
    #                 else:
    #                     city_id = self.env['feosco.city'].create({
    #                         'name' : pro_name,
    #                         'code' : pro_code,
    #                         'country_id' : self.env.ref('base.vn').id
    #                     })
    #                     print "----- Tao TP : %s" % (pro_name)
    #
    #                 with open('%s/vietnam-subdivisions/provinces/%s/districts.json' % (dir_path,pro_code)) as districts:
    #                     districts = json.load(districts)
    #                     for distr in districts:
    #                         distr_code = distr.get('LocationID', False).strip()
    #                         distr_name = distr.get('LocationName', False).strip()
    #                         if distr_code:
    #                             distr_id = self.env['feosco.district'].search([('name','=',distr_name),('city_id','=',city_id.id)])
    #                             if distr_id:
    #                                 distr_id.code = distr_code
    #                                 print "+++ Update huyen : %s" % (distr_name)
    #                             else:
    #                                 distr_id = self.env['feosco.district'].create({
    #                                     'name': distr_name,
    #                                     'code': distr_code,
    #                                     'city_id': city_id.id
    #                                 })
    #                                 print "+++ Tao huyen : %s" % (distr_name)
    #
    #                             with open('%s/vietnam-subdivisions/provinces/%s/districts/%s/towns.json' % (dir_path, pro_code,distr_code)) as wards:
    #                                 wards = json.load(wards)
    #                                 for ward in wards:
    #                                     ward_code = ward.get('LocationID', False).strip()
    #                                     ward_name = ward.get('LocationName', False).strip()
    #                                     ward_id = self.env['feosco.ward'].search([('name', '=', ward_name), ('district_id', '=', distr_id.id)])
    #                                     if ward_id:
    #                                         ward_id.code = ward_code
    #                                         print "Update xa : %s" % (ward_name)
    #                                     else:
    #                                         ward_id = self.env['feosco.ward'].create({
    #                                             'name': ward_name,
    #                                             'code': ward_code,
    #                                             'district_id': distr_id.id
    #                                         })
    #                                         print "Tao xa : %s" % (ward_name)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
