# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta, MO
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import StringIO
import xlsxwriter
import base64


class bao_cao_kiem_kho(models.Model):
    _name = 'bao.cao.kiem.kho'

    type_report = fields.Selection(
        [('so_ma_lech', 'Báo cáo số mã lệch'), ('so_luong_lech', 'Báo cáo số lượng lệch'), ('all', 'Cả hai')],
        default='so_ma_lech', string='Loại báo cáo')
    type_time = fields.Selection([('tuan', 'Tuần'), ('thang', 'Tháng')], default='tuan', string='Loại thời gian')
    start_date = fields.Date(string='Từ Ngày', required=1, default=datetime.now())
    end_date = fields.Date(string='Đến Ngày', compute='onchange_start_date')
    duration = fields.Integer(string='Số lượng tuần/tháng', default=1)
    bao_cao_sml_table1_ids = fields.One2many('bao.cao.sml.table1', 'bao_cao_kiem_kho_id', compute='onchange_end_date')
    bao_cao_sml_table2_ids = fields.One2many('bao.cao.sml.table2', 'bao_cao_kiem_kho_id', compute='onchange_end_date')
    bao_cao_sml_table3_ids = fields.One2many('bao.cao.sml.table3', 'bao_cao_kiem_kho_id', compute='onchange_end_date')
    bao_cao_sml_table4_ids = fields.One2many('bao.cao.sml.table4', 'bao_cao_kiem_kho_id', compute='onchange_end_date')
    bao_cao_sml_table5_ids = fields.One2many('bao.cao.sml.table5', 'bao_cao_kiem_kho_id', compute='onchange_end_date')
    bao_cao_sml_table6_ids = fields.One2many('bao.cao.sml.table6', 'bao_cao_kiem_kho_id', compute='onchange_end_date')
    bao_cao_sml_table7_ids = fields.One2many('bao.cao.sml.table7', 'bao_cao_kiem_kho_id', compute='onchange_end_date')
    bao_cao_sml_table8_ids = fields.One2many('bao.cao.sml.table8', 'bao_cao_kiem_kho_id', compute='onchange_end_date')
    bao_cao_sml_table9_ids = fields.One2many('bao.cao.sml.table9', 'bao_cao_kiem_kho_id', compute='onchange_end_date')

    def get_inventory_by_condition(self):
        domain = [('validate_date', '>=', self.start_date), ('validate_date', '<=', self.end_date),
                  ('state', '=', 'done')]
        inventory_ids = self.env['stock.inventory'].search(domain)
        return inventory_ids

    def get_bao_cao_sml_table1(self):
        self.bao_cao_sml_table1_ids = []
        inventory_ids = self.get_inventory_by_condition()
        if inventory_ids:
            query = """SELECT validate_date, count(id) FROM stock_inventory_line WHERE inventory_id in (%s) GROUP BY validate_date;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT validate_date, count(id) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 GROUP BY validate_date;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            data = {}
            for date_kiem in inventory_line_sp_kiem:
                data.update({
                    date_kiem[0]: {
                        'date': date_kiem[0],
                        'count_sp_lech': 0,
                        'count_sp_kiem': int(date_kiem[1]),
                    }
                })

            for date_lech in inventory_line_sp_lech:
                old_data = data.get(date_lech[0])
                old_data.update({
                    'count_sp_lech': int(date_lech[1]),
                })
                data.update({
                    date_lech[0]: old_data
                })
            for key, value in data.items():
                self.bao_cao_sml_table1_ids += self.bao_cao_sml_table1_ids.new({
                    'date': value.get('date', False),
                    'count_sp_lech': value.get('count_sp_lech', 0),
                    'count_sp_kiem': value.get('count_sp_kiem', 0),
                    'ty_le': float(value.get('count_sp_lech', 0)) / float(value.get('count_sp_kiem', 0)) * 100,
                })

    def get_bao_cao_sml_table2(self):
        self.bao_cao_sml_table2_ids = []
        inventory_ids = self.get_inventory_by_condition()
        if inventory_ids:
            query = """SELECT validate_weeked, count(id) FROM stock_inventory_line WHERE inventory_id in (%s) GROUP BY validate_weeked;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT validate_weeked, count(id) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 GROUP BY validate_weeked;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            query = """SELECT validate_weeked, count(DISTINCT product_id) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 GROUP BY validate_weeked;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_khong_trung = self.env.cr.fetchall()
            data = {}
            for week_kiem in inventory_line_sp_kiem:
                data.update({
                    week_kiem[0]: {
                        'week': week_kiem[0],
                        'count_sp_lech': 0,
                        'count_sp_kiem': int(week_kiem[1]),
                    }
                })

            for week_lech in inventory_line_sp_lech:
                old_data = data.get(week_lech[0])
                old_data.update({
                    'count_sp_lech': int(week_lech[1]),
                })
                data.update({
                    week_lech[0]: old_data
                })
            for week_khong_trung in inventory_line_sp_khong_trung:
                old_data = data.get(week_khong_trung[0])
                old_data.update({
                    'count_sp_khong_trung': int(week_khong_trung[1]),
                })
                data.update({
                    week_khong_trung[0]: old_data
                })
            product_ids = self.env['product.product'].search([])
            for key, value in data.items():
                self.bao_cao_sml_table2_ids += self.bao_cao_sml_table2_ids.new({
                    'week': value.get('week', False),
                    'count_sp_lech': value.get('count_sp_lech', 0),
                    'count_sp_kiem': value.get('count_sp_kiem', 0),
                    'ty_le': float(value.get('count_sp_lech', 0)) / float(value.get('count_sp_kiem', 0)) * 100,
                    'count_sp_duy_nhat': value.get('count_sp_khong_trung', 0),
                    'count_sp_active': len(product_ids),
                    'ty_le_sp': float(value.get('count_sp_khong_trung', 0)) / float(len(product_ids)) * 100,
                })

    def get_bao_cao_sml_table3(self):
        week_start = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).isocalendar()[1]
        week_end = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).isocalendar()[1]
        week_sub = 0
        if week_start > week_end:
            week_sub = week_end
            week_end = 52
        product_category_ids = self.env['product.category'].search([('parent_id', '=', False)])
        self.bao_cao_sml_table3_ids = []
        for week in range(week_start, week_end + 1):
            count_sp_lech = 0
            count_sp_kiem = 0
            for product_category_id in product_category_ids:
                line_sml_table3 = self.get_line_sml_table3(product_category_id.id, week)
                count_sp_lech += line_sml_table3.get('count_sp_lech', 0)
                count_sp_kiem += line_sml_table3.get('count_sp_kiem', 0)
                ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
                self.bao_cao_sml_table3_ids += self.bao_cao_sml_table3_ids.new(line_sml_table3)
            self.bao_cao_sml_table3_ids += self.bao_cao_sml_table3_ids.new({
                'week': week,
                'count_sp_lech': count_sp_lech,
                'count_sp_kiem': count_sp_kiem,
                'ty_le': ty_le,
            })
        if week_sub:
            for week in range(1, week_sub + 1):
                count_sp_lech = 0
                count_sp_kiem = 0
                for product_category_id in product_category_ids:
                    line_sml_table3 = self.get_line_sml_table3(product_category_id.id, week)
                    count_sp_lech += line_sml_table3.get('count_sp_lech', 0)
                    count_sp_kiem += line_sml_table3.get('count_sp_kiem', 0)
                    ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
                    self.bao_cao_sml_table3_ids += self.bao_cao_sml_table3_ids.new(line_sml_table3)
                self.bao_cao_sml_table3_ids += self.bao_cao_sml_table3_ids.new({
                    'week': week,
                    'count_sp_lech': count_sp_lech,
                    'count_sp_kiem': count_sp_kiem,
                    'ty_le': ty_le,
                })

    def get_line_sml_table3(self, product_category_id, validate_weeked):
        inventory_ids = self.get_inventory_by_condition()
        count_sp_lech = 0
        count_sp_kiem = 0
        ty_le = 0
        if inventory_ids:
            query = """SELECT count(id) FROM stock_inventory_line WHERE inventory_id in (%s) AND product_category_id = %s AND validate_weeked = %s;""" \
                    % (', '.join(str(id) for id in inventory_ids.ids), product_category_id, validate_weeked)
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT count(id) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 AND product_category_id = %s AND validate_weeked = %s;""" % (
                ', '.join(str(id) for id in inventory_ids.ids), product_category_id, validate_weeked)
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            count_sp_lech = inventory_line_sp_lech[0][0]
            count_sp_kiem = inventory_line_sp_kiem[0][0]
            ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
        return {
            'week': validate_weeked,
            'product_category_id': product_category_id,
            'count_sp_lech': count_sp_lech,
            'count_sp_kiem': count_sp_kiem,
            'ty_le': ty_le,
        }

    def get_bao_cao_sml_table4(self):
        self.bao_cao_sml_table4_ids = []
        inventory_ids = self.get_inventory_by_condition()
        if inventory_ids:
            query = """SELECT validate_month, count(id) FROM stock_inventory_line WHERE inventory_id in (%s) GROUP BY validate_month;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT validate_month, count(id) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 GROUP BY validate_month;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            query = """SELECT validate_month, count(DISTINCT product_id) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 GROUP BY validate_month;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_khong_trung = self.env.cr.fetchall()
            data = {}
            for month_kiem in inventory_line_sp_kiem:
                data.update({
                    month_kiem[0]: {
                        'month': month_kiem[0],
                        'count_sp_lech': 0,
                        'count_sp_kiem': int(month_kiem[1]),
                    }
                })

            for month_lech in inventory_line_sp_lech:
                old_data = data.get(month_lech[0])
                old_data.update({
                    'count_sp_lech': int(month_lech[1]),
                })
                data.update({
                    month_lech[0]: old_data
                })
            for month_khong_trung in inventory_line_sp_khong_trung:
                old_data = data.get(month_khong_trung[0])
                old_data.update({
                    'count_sp_khong_trung': int(month_khong_trung[1]),
                })
                data.update({
                    month_khong_trung[0]: old_data
                })
            product_ids = self.env['product.product'].search([])
            for key, value in data.items():
                self.bao_cao_sml_table4_ids += self.bao_cao_sml_table4_ids.new({
                    'month': value.get('month', False),
                    'count_sp_lech': value.get('count_sp_lech', 0),
                    'count_sp_kiem': value.get('count_sp_kiem', 0),
                    'ty_le': float(value.get('count_sp_lech', 0)) / float(value.get('count_sp_kiem', 0)) * 100,
                    'count_sp_duy_nhat': value.get('count_sp_khong_trung', 0),
                    'count_sp_active': len(product_ids),
                    'ty_le_sp': float(value.get('count_sp_khong_trung', 0)) / float(len(product_ids)) * 100,
                })

    def get_bao_cao_sml_table5(self):
        month_start = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).month
        month_end = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).month
        month_sub = 0
        if month_start > month_end:
            month_sub = month_end
            month_end = 12
        product_category_ids = self.env['product.category'].search([('parent_id', '=', False)])
        self.bao_cao_sml_table5_ids = []
        for month in range(month_start, month_end + 1):
            count_sp_lech = 0
            count_sp_kiem = 0
            for product_category_id in product_category_ids:
                line_sml_table5 = self.get_line_sml_table5(product_category_id.id, month)
                count_sp_lech += line_sml_table5.get('count_sp_lech', 0)
                count_sp_kiem += line_sml_table5.get('count_sp_kiem', 0)
                ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
                self.bao_cao_sml_table5_ids += self.bao_cao_sml_table5_ids.new(line_sml_table5)
            self.bao_cao_sml_table5_ids += self.bao_cao_sml_table5_ids.new({
                'month': month,
                'count_sp_lech': count_sp_lech,
                'count_sp_kiem': count_sp_kiem,
                'ty_le': ty_le,
            })
        if month_sub:
            for month in range(1, month_sub + 1):
                count_sp_lech = 0
                count_sp_kiem = 0
                for product_category_id in product_category_ids:
                    line_sml_table5 = self.get_line_sml_table5(product_category_id.id, month)
                    count_sp_lech += line_sml_table5.get('count_sp_lech', 0)
                    count_sp_kiem += line_sml_table5.get('count_sp_kiem', 0)
                    ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
                    self.bao_cao_sml_table5_ids += self.bao_cao_sml_table5_ids.new(line_sml_table5)
                self.bao_cao_sml_table5_ids += self.bao_cao_sml_table5_ids.new({
                    'month': month,
                    'count_sp_lech': count_sp_lech,
                    'count_sp_kiem': count_sp_kiem,
                    'ty_le': ty_le,
                })

    def get_line_sml_table5(self, product_category_id, validate_month):
        inventory_ids = self.get_inventory_by_condition()
        count_sp_lech = 0
        count_sp_kiem = 0
        ty_le = 0
        if inventory_ids:
            query = """SELECT count(id) FROM stock_inventory_line WHERE inventory_id in (%s) AND product_category_id = %s AND validate_month = %s;""" \
                    % (', '.join(str(id) for id in inventory_ids.ids), product_category_id, validate_month)
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT count(id) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 AND product_category_id = %s AND validate_month = %s;""" % (
                ', '.join(str(id) for id in inventory_ids.ids), product_category_id, validate_month)
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            count_sp_lech = inventory_line_sp_lech[0][0]
            count_sp_kiem = inventory_line_sp_kiem[0][0]
            ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
        return {
            'month': validate_month,
            'product_category_id': product_category_id,
            'count_sp_lech': count_sp_lech,
            'count_sp_kiem': count_sp_kiem,
            'ty_le': ty_le,
        }

    def get_bao_cao_sml_table6(self):
        self.bao_cao_sml_table6_ids = []
        inventory_ids = self.get_inventory_by_condition()
        if inventory_ids:
            query = """SELECT validate_weeked, sum(theoretical_qty) FROM stock_inventory_line WHERE inventory_id in (%s) GROUP BY validate_weeked;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT validate_weeked, sum(Abs(diff_qty)) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 GROUP BY validate_weeked;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            data = {}
            for week_kiem in inventory_line_sp_kiem:
                data.update({
                    week_kiem[0]: {
                        'week': week_kiem[0],
                        'count_sp_lech': 0,
                        'count_sp_kiem': int(week_kiem[1]),
                    }
                })

            for week_lech in inventory_line_sp_lech:
                old_data = data.get(week_lech[0])
                old_data.update({
                    'count_sp_lech': int(week_lech[1]),
                })
                data.update({
                    week_lech[0]: old_data
                })
            for key, value in data.items():
                self.bao_cao_sml_table6_ids += self.bao_cao_sml_table6_ids.new({
                    'week': value.get('week', False),
                    'count_sp_lech': value.get('count_sp_lech', 0),
                    'count_sp_kiem': value.get('count_sp_kiem', 0),
                    'ty_le': float(value.get('count_sp_lech', 0)) / float(value.get('count_sp_kiem', 0)) * 100,
                })

    def get_bao_cao_sml_table7(self):
        week_start = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).isocalendar()[1]
        week_end = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).isocalendar()[1]
        week_sub = 0
        if week_start > week_end:
            week_sub = week_end
            week_end = 52
        product_category_ids = self.env['product.category'].search([('parent_id', '=', False)])
        self.bao_cao_sml_table7_ids = []
        for week in range(week_start, week_end + 1):
            count_sp_lech = 0
            count_sp_kiem = 0
            for product_category_id in product_category_ids:
                line_sml_table7 = self.get_line_sml_table7(product_category_id.id, week)
                count_sp_lech += line_sml_table7.get('count_sp_lech', 0)
                count_sp_kiem += line_sml_table7.get('count_sp_kiem', 0)
                ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
                self.bao_cao_sml_table7_ids += self.bao_cao_sml_table7_ids.new(line_sml_table7)
            self.bao_cao_sml_table7_ids += self.bao_cao_sml_table7_ids.new({
                'week': week,
                'count_sp_lech': count_sp_lech,
                'count_sp_kiem': count_sp_kiem,
                'ty_le': ty_le,
            })
        if week_sub:
            for week in range(1, week_sub + 1):
                count_sp_lech = 0
                count_sp_kiem = 0
                for product_category_id in product_category_ids:
                    line_sml_table7 = self.get_line_sml_table7(product_category_id.id, week)
                    count_sp_lech += line_sml_table7.get('count_sp_lech', 0)
                    count_sp_kiem += line_sml_table7.get('count_sp_kiem', 0)
                    ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
                    self.bao_cao_sml_table7_ids += self.bao_cao_sml_table7_ids.new(line_sml_table7)
                self.bao_cao_sml_table7_ids += self.bao_cao_sml_table7_ids.new({
                    'week': week,
                    'count_sp_lech': count_sp_lech,
                    'count_sp_kiem': count_sp_kiem,
                    'ty_le': ty_le,
                })

    def get_line_sml_table7(self, product_category_id, validate_weeked):
        inventory_ids = self.get_inventory_by_condition()
        count_sp_lech = 0
        count_sp_kiem = 0
        ty_le = 0
        if inventory_ids:
            query = """SELECT sum(theoretical_qty) FROM stock_inventory_line WHERE inventory_id in (%s) AND product_category_id = %s AND validate_weeked = %s GROUP BY validate_weeked;""" \
                    % (', '.join(str(id) for id in inventory_ids.ids), product_category_id, validate_weeked)
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT sum(Abs(diff_qty)) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 AND product_category_id = %s AND validate_weeked = %s GROUP BY validate_weeked;""" % (
                ', '.join(str(id) for id in inventory_ids.ids), product_category_id, validate_weeked)
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            count_sp_lech = 0
            if inventory_line_sp_lech and inventory_line_sp_lech[0]:
                count_sp_lech = inventory_line_sp_lech[0][0]
            count_sp_kiem = 0
            if inventory_line_sp_kiem and inventory_line_sp_kiem[0]:
                count_sp_kiem = inventory_line_sp_kiem[0][0]
            ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
        return {
            'week': validate_weeked,
            'product_category_id': product_category_id,
            'count_sp_lech': count_sp_lech,
            'count_sp_kiem': count_sp_kiem,
            'ty_le': ty_le,
        }

    def get_bao_cao_sml_table8(self):
        self.bao_cao_sml_table8_ids = []
        inventory_ids = self.get_inventory_by_condition()
        if inventory_ids:
            query = """SELECT validate_month, sum(theoretical_qty) FROM stock_inventory_line WHERE inventory_id in (%s) GROUP BY validate_month;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT validate_month, sum(Abs(diff_qty)) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 GROUP BY validate_month;""" % (
                ', '.join(str(id) for id in inventory_ids.ids))
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            data = {}
            for month_kiem in inventory_line_sp_kiem:
                data.update({
                    month_kiem[0]: {
                        'month': month_kiem[0],
                        'count_sp_lech': 0,
                        'count_sp_kiem': int(month_kiem[1]),
                    }
                })

            for month_lech in inventory_line_sp_lech:
                old_data = data.get(month_lech[0])
                old_data.update({
                    'count_sp_lech': int(month_lech[1]),
                })
                data.update({
                    month_lech[0]: old_data
                })
            for key, value in data.items():
                self.bao_cao_sml_table8_ids += self.bao_cao_sml_table8_ids.new({
                    'month': value.get('month', False),
                    'count_sp_lech': value.get('count_sp_lech', 0),
                    'count_sp_kiem': value.get('count_sp_kiem', 0),
                    'ty_le': float(value.get('count_sp_lech', 0)) / float(value.get('count_sp_kiem', 0)) * 100,
                })

    def get_bao_cao_sml_table9(self):
        month_start = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).month
        month_end = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).month
        month_sub = 0
        if month_start > month_end:
            month_sub = month_end
            month_end = 12
        product_category_ids = self.env['product.category'].search([('parent_id', '=', False)])
        self.bao_cao_sml_table9_ids = []
        for month in range(month_start, month_end + 1):
            count_sp_lech = 0
            count_sp_kiem = 0
            for product_category_id in product_category_ids:
                line_sml_table9 = self.get_line_sml_table9(product_category_id.id, month)
                count_sp_lech += line_sml_table9.get('count_sp_lech', 0)
                count_sp_kiem += line_sml_table9.get('count_sp_kiem', 0)
                ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
                self.bao_cao_sml_table9_ids += self.bao_cao_sml_table9_ids.new(line_sml_table9)
            self.bao_cao_sml_table9_ids += self.bao_cao_sml_table9_ids.new({
                'month': month,
                'count_sp_lech': count_sp_lech,
                'count_sp_kiem': count_sp_kiem,
                'ty_le': ty_le,
            })
        if month_sub:
            for month in range(1, month_sub + 1):
                count_sp_lech = 0
                count_sp_kiem = 0
                for product_category_id in product_category_ids:
                    line_sml_table9 = self.get_line_sml_table9(product_category_id.id, month)
                    count_sp_lech += line_sml_table9.get('count_sp_lech', 0)
                    count_sp_kiem += line_sml_table9.get('count_sp_kiem', 0)
                    ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
                    self.bao_cao_sml_table9_ids += self.bao_cao_sml_table9_ids.new(line_sml_table9)
                self.bao_cao_sml_table9_ids += self.bao_cao_sml_table9_ids.new({
                    'month': month,
                    'count_sp_lech': count_sp_lech,
                    'count_sp_kiem': count_sp_kiem,
                    'ty_le': ty_le,
                })

    def get_line_sml_table9(self, product_category_id, validate_month):
        inventory_ids = self.get_inventory_by_condition()
        count_sp_lech = 0
        count_sp_kiem = 0
        ty_le = 0
        if inventory_ids:
            query = """SELECT sum(theoretical_qty) FROM stock_inventory_line WHERE inventory_id in (%s) AND product_category_id = %s AND validate_month = %s GROUP BY validate_month;""" \
                    % (', '.join(str(id) for id in inventory_ids.ids), product_category_id, validate_month)
            self.env.cr.execute(query)
            inventory_line_sp_kiem = self.env.cr.fetchall()
            query = """SELECT sum(Abs(diff_qty)) FROM stock_inventory_line WHERE inventory_id in (%s) AND diff_qty != 0 AND product_category_id = %s AND validate_month = %s GROUP BY validate_month;""" % (
                ', '.join(str(id) for id in inventory_ids.ids), product_category_id, validate_month)
            self.env.cr.execute(query)
            inventory_line_sp_lech = self.env.cr.fetchall()
            count_sp_lech = 0
            if inventory_line_sp_lech and inventory_line_sp_lech[0]:
                count_sp_lech = inventory_line_sp_lech[0][0]
            count_sp_kiem = 0
            if inventory_line_sp_kiem and inventory_line_sp_kiem[0]:
                count_sp_kiem = inventory_line_sp_kiem[0][0]
            ty_le = 0 if count_sp_kiem == 0 else float(count_sp_lech) / float(count_sp_kiem) * 100
        return {
            'month': validate_month,
            'product_category_id': product_category_id,
            'count_sp_lech': count_sp_lech,
            'count_sp_kiem': count_sp_kiem,
            'ty_le': ty_le,
        }

    @api.onchange('type_time', 'start_date', 'duration')
    def onchange_start_date(self):
        if self.start_date:
            if self.duration <= 0:
                self.duration = 1
            date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT)
            if self.type_time == 'tuan':
                start_date = date + relativedelta(weekday=MO(-1))
                end_date = start_date + timedelta(days=6 * self.duration)
                if start_date != date:
                    self.start_date = start_date
                self.end_date = end_date
                print
                "%s %s" % (start_date, end_date)
            elif self.type_time == 'thang':
                start_date = date.replace(day=1)
                end_date = start_date + relativedelta(months=1 * self.duration, day=1, days=-1)
                if start_date != date:
                    self.start_date = start_date
                self.end_date = end_date
                print
                "%s %s" % (start_date, end_date)

    @api.onchange('start_date')
    def onchange_end_date(self):
        self.get_bao_cao_sml_table1()
        self.get_bao_cao_sml_table2()
        self.get_bao_cao_sml_table3()
        self.get_bao_cao_sml_table4()
        self.get_bao_cao_sml_table5()
        self.get_bao_cao_sml_table6()
        self.get_bao_cao_sml_table7()
        self.get_bao_cao_sml_table8()
        self.get_bao_cao_sml_table9()

    @api.multi
    def print_excel_inventory_adjustment(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet_1 = workbook.add_worksheet('Data kiểm số mã SP-Ngày')
        worksheet_2 = workbook.add_worksheet('RP_Mã số Lệch')
        worksheet_3 = workbook.add_worksheet('RP_Số lượng lệch')
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        text_bold = workbook.add_format({'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        text_style_red = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'right', 'valign': 'vcenter', 'color': 'red'})
        text_style_right = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'right', 'valign': 'vcenter'})
        text_style_left = workbook.add_format({'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter'})
        text_style_center = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'center', 'valign': 'vcenter'})

        # Data kiểm số mã SP - Ngày
        worksheet_1.set_column('A:A', 16)
        worksheet_1.set_column('B:B', 16)
        worksheet_1.set_column('C:C', 16)
        worksheet_1.set_column('D:D', 16)

        row = 0
        summary_header_1 = ['Ngày', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
        [worksheet_1.write(row, header_cell, unicode(summary_header_1[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header_1)) if summary_header_1[header_cell]]
        for line in self.bao_cao_sml_table1_ids:
            row += 1

            worksheet_1.write(row, 0, line.date, text_style_center)
            worksheet_1.write(row, 1, line.count_sp_lech, text_style_right)
            worksheet_1.write(row, 2, line.count_sp_kiem, text_style_right)
            worksheet_1.write(row, 3, line.ty_le, text_style_red)

        # RP_Mã số Lệch
        worksheet_2.set_column('A:P', 15)

        if self.type_time == 'tuan':
            worksheet_2.merge_range('A1:G1', unicode(("BÁO CÁO KIỂM SỐ MÃ SP - TUẦN"), "utf-8"), text_bold)
            row = 1
            summary_header_21 = ['Tuần', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)', 'SL mã SP duy nhất (tuần)',
                                 'Số mã đang kinh doanh', 'Tỉ lệ (%)']
            [worksheet_2.write(row, header_cell, unicode(summary_header_21[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header_21)) if summary_header_21[header_cell]]
            for line in self.bao_cao_sml_table2_ids:
                row += 1

                worksheet_2.write(row, 0, line.week, text_style_center)
                worksheet_2.write(row, 1, line.count_sp_lech, text_style_right)
                worksheet_2.write(row, 2, line.count_sp_kiem, text_style_right)
                worksheet_2.write(row, 3, line.ty_le, text_style_red)
                worksheet_2.write(row, 4, line.count_sp_duy_nhat, text_style_right)
                worksheet_2.write(row, 5, line.count_sp_active, text_style_right)
                worksheet_2.write(row, 6, line.ty_le_sp, text_style_red)

            row += 5
            worksheet_2.merge_range('A%s:E%s' % (row, row),
                                    unicode(("BÁO CÁO KIỂM SỐ MÃ SP THEO DANH MỤC SẢN PHẨM - TUẦN"), "utf-8"),
                                    text_bold)
            summary_header_22 = ['Tuần', 'Danh mục sản phẩm', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_2.write(row, header_cell, unicode(summary_header_22[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header_22)) if summary_header_22[header_cell]]
            for line in self.bao_cao_sml_table3_ids:
                row += 1

                worksheet_2.write(row, 0, line.week, text_style_center)
                worksheet_2.write(row, 1, line.product_category_id.name or 'Total', text_style_left)
                worksheet_2.write(row, 2, line.count_sp_lech, text_style_right)
                worksheet_2.write(row, 3, line.count_sp_kiem, text_style_right)
                worksheet_2.write(row, 4, line.ty_le, text_style_red)

        if self.type_time == 'thang':
            worksheet_2.merge_range('A1:G1', unicode(("BÁO CÁO KIỂM SỐ MÃ SP - TUẦN"), "utf-8"), text_bold)
            row = 1
            summary_header_21 = ['Tuần', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)', 'SL mã SP duy nhất (tuần)',
                                 'Số mã đang kinh doanh', 'Tỉ lệ (%)']
            [worksheet_2.write(row, header_cell, unicode(summary_header_21[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header_21)) if summary_header_21[header_cell]]
            for line in self.bao_cao_sml_table2_ids:
                row += 1

                worksheet_2.write(row, 0, line.week, text_style_center)
                worksheet_2.write(row, 1, line.count_sp_lech, text_style_right)
                worksheet_2.write(row, 2, line.count_sp_kiem, text_style_right)
                worksheet_2.write(row, 3, line.ty_le, text_style_red)
                worksheet_2.write(row, 4, line.count_sp_duy_nhat, text_style_right)
                worksheet_2.write(row, 5, line.count_sp_active, text_style_right)
                worksheet_2.write(row, 6, line.ty_le_sp, text_style_red)

            row += 5
            worksheet_2.merge_range('A%s:E%s' % (row, row),
                                    unicode(("BÁO CÁO KIỂM SỐ MÃ SP THEO DANH MỤC SẢN PHẨM - TUẦN"), "utf-8"),
                                    text_bold)
            summary_header_22 = ['Tuần', 'Danh mục sản phẩm', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_2.write(row, header_cell, unicode(summary_header_22[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header_22)) if summary_header_22[header_cell]]
            for line in self.bao_cao_sml_table3_ids:
                row += 1

                worksheet_2.write(row, 0, line.week, text_style_center)
                worksheet_2.write(row, 1, line.product_category_id.name or 'Total', text_style_left)
                worksheet_2.write(row, 2, line.count_sp_lech, text_style_right)
                worksheet_2.write(row, 3, line.count_sp_kiem, text_style_right)
                worksheet_2.write(row, 4, line.ty_le, text_style_red)

            # --------------------------
            worksheet_2.merge_range('J1:P1', unicode(("BÁO CÁO KIỂM SỐ MÃ SP - THÁNG"), "utf-8"), text_bold)
            row = 1
            col = 9
            summary_header_21 = ['Tháng', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)', 'SL mã SP duy nhất (tuần)',
                                 'Số mã đang kinh doanh', 'Tỉ lệ (%)']
            [worksheet_2.write(row, col + header_cell, unicode(summary_header_21[header_cell], "utf-8"),
                               body_bold_color) for
             header_cell in range(0, len(summary_header_21)) if summary_header_21[header_cell]]
            for line in self.bao_cao_sml_table4_ids:
                row += 1

                worksheet_2.write(row, 9, line.month, text_style_center)
                worksheet_2.write(row, 10, line.count_sp_lech, text_style_right)
                worksheet_2.write(row, 11, line.count_sp_kiem, text_style_right)
                worksheet_2.write(row, 12, line.ty_le, text_style_red)
                worksheet_2.write(row, 13, line.count_sp_duy_nhat, text_style_right)
                worksheet_2.write(row, 14, line.count_sp_active, text_style_right)
                worksheet_2.write(row, 15, line.ty_le_sp, text_style_red)

            row += 5
            worksheet_2.merge_range('J%s:N%s' % (row, row),
                                    unicode(("BÁO CÁO KIỂM SỐ MÃ SP THEO DANH MỤC SẢN PHẨM - THÁNG"), "utf-8"),
                                    text_bold)
            summary_header_22 = ['Tháng', 'Danh mục sản phẩm', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_2.write(row, col + header_cell, unicode(summary_header_22[header_cell], "utf-8"),
                               body_bold_color) for
             header_cell in range(0, len(summary_header_22)) if summary_header_22[header_cell]]
            for line in self.bao_cao_sml_table5_ids:
                row += 1

                worksheet_2.write(row, 9, line.month, text_style_center)
                worksheet_2.write(row, 10, line.product_category_id.name or 'Total', text_style_left)
                worksheet_2.write(row, 11, line.count_sp_lech, text_style_right)
                worksheet_2.write(row, 12, line.count_sp_kiem, text_style_right)
                worksheet_2.write(row, 13, line.ty_le, text_style_red)

        # RP_Số lượng lệch
        worksheet_3.set_column('A:P', 15)

        if self.type_time == 'tuan':
            worksheet_3.merge_range('A1:E1', unicode(("BÁO CÁO KIỂM SỐ LƯỢNG SP - TUẦN"), "utf-8"), text_bold)
            row = 1
            summary_header_31 = ['Tuần', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_3.write(row, header_cell, unicode(summary_header_31[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header_31)) if summary_header_31[header_cell]]
            for line in self.bao_cao_sml_table6_ids:
                row += 1

                worksheet_3.write(row, 0, line.week, text_style_center)
                worksheet_3.write(row, 1, line.count_sp_lech, text_style_right)
                worksheet_3.write(row, 2, line.count_sp_kiem, text_style_right)
                worksheet_3.write(row, 3, line.ty_le, text_style_red)

            row += 5
            worksheet_3.merge_range('A%s:E%s' % (row, row),
                                    unicode(("BÁO CÁO KIỂM SỐ LƯỢNG SP THEO DANH MỤC SẢN PHẨM - TUẦN"), "utf-8"),
                                    text_bold)
            summary_header_32 = ['Tuần', 'Danh mục sản phẩm', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_3.write(row, header_cell, unicode(summary_header_32[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header_32)) if summary_header_32[header_cell]]
            for line in self.bao_cao_sml_table7_ids:
                row += 1

                worksheet_3.write(row, 0, line.week, text_style_center)
                worksheet_3.write(row, 1, line.product_category_id.name or 'Total', text_style_left)
                worksheet_3.write(row, 2, line.count_sp_lech, text_style_right)
                worksheet_3.write(row, 3, line.count_sp_kiem, text_style_right)
                worksheet_3.write(row, 4, line.ty_le, text_style_red)

        if self.type_time == 'thang':
            worksheet_3.merge_range('A1:E1', unicode(("BÁO CÁO KIỂM SỐ LƯỢNG SP - TUẦN"), "utf-8"), text_bold)
            row = 1
            summary_header_31 = ['Tuần', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_3.write(row, header_cell, unicode(summary_header_31[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header_31)) if summary_header_31[header_cell]]
            for line in self.bao_cao_sml_table6_ids:
                row += 1

                worksheet_3.write(row, 0, line.week, text_style_center)
                worksheet_3.write(row, 1, line.count_sp_lech, text_style_right)
                worksheet_3.write(row, 2, line.count_sp_kiem, text_style_right)
                worksheet_3.write(row, 3, line.ty_le, text_style_red)

            row += 5
            worksheet_3.merge_range('A%s:E%s' % (row, row),
                                    unicode(("BÁO CÁO KIỂM SỐ LƯỢNG SP THEO DANH MỤC SẢN PHẨM - TUẦN"), "utf-8"),
                                    text_bold)
            summary_header_32 = ['Tuần', 'Danh mục sản phẩm', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_3.write(row, header_cell, unicode(summary_header_32[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header_32)) if summary_header_32[header_cell]]
            for line in self.bao_cao_sml_table7_ids:
                row += 1

                worksheet_3.write(row, 0, line.week, text_style_center)
                worksheet_3.write(row, 1, line.product_category_id.name or 'Total', text_style_left)
                worksheet_3.write(row, 2, line.count_sp_lech, text_style_right)
                worksheet_3.write(row, 3, line.count_sp_kiem, text_style_right)
                worksheet_3.write(row, 4, line.ty_le, text_style_red)

            # --------------------------
            worksheet_3.merge_range('J1:N1', unicode(("BÁO CÁO KIỂM SỐ LƯỢNG SP - THÁNG"), "utf-8"), text_bold)
            row = 1
            col = 9
            summary_header_31 = ['Tháng', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_3.write(row, col + header_cell, unicode(summary_header_31[header_cell], "utf-8"),
                               body_bold_color) for
             header_cell in range(0, len(summary_header_31)) if summary_header_31[header_cell]]
            for line in self.bao_cao_sml_table8_ids:
                row += 1

                worksheet_3.write(row, 9, line.month, text_style_center)
                worksheet_3.write(row, 10, line.count_sp_lech, text_style_right)
                worksheet_3.write(row, 11, line.count_sp_kiem, text_style_right)
                worksheet_3.write(row, 12, line.ty_le, text_style_red)

            row += 5
            worksheet_3.merge_range('J%s:N%s' % (row, row),
                                    unicode(("BÁO CÁO KIỂM SỐ LƯỢNG SP THEO DANH MỤC SẢN PHẨM - THÁNG"), "utf-8"),
                                    text_bold)
            summary_header_32 = ['Tháng', 'Danh mục sản phẩm', 'Số mã SP bị lệch', 'Số mã SP kiểm', 'Tỉ lệ (%)']
            [worksheet_3.write(row, col + header_cell, unicode(summary_header_32[header_cell], "utf-8"),
                               body_bold_color) for
             header_cell in range(0, len(summary_header_32)) if summary_header_32[header_cell]]
            for line in self.bao_cao_sml_table9_ids:
                row += 1

                worksheet_3.write(row, 9, line.month, text_style_center)
                worksheet_3.write(row, 10, line.product_category_id.name or 'Total', text_style_left)
                worksheet_3.write(row, 11, line.count_sp_lech, text_style_right)
                worksheet_3.write(row, 12, line.count_sp_kiem, text_style_right)
                worksheet_3.write(row, 13, line.ty_le, text_style_red)

        start_day = datetime.strptime(self.start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
        end_day = datetime.strptime(self.end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
        name_file = 'Báo cáo kiểm kho' + '_' + start_day + '_' + end_day + '.xlsx'
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': name_file, 'datas_fname': name_file, 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}


class bao_cao_sml_table1(models.Model):
    _name = 'bao.cao.sml.table1'

    date = fields.Date(string='Ngày')
    count_sp_lech = fields.Integer(string='Số mã SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số mã SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')


class bao_cao_sml_table2(models.Model):
    _name = 'bao.cao.sml.table2'

    week = fields.Integer(string='Tuần')
    count_sp_lech = fields.Integer(string='Số mã SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số mã SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    count_sp_duy_nhat = fields.Integer(string='SL mã SP duy nhất (tuần)')
    count_sp_active = fields.Integer(string='Số mã đang kinh doanh')
    ty_le_sp = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')


class bao_cao_sml_table3(models.Model):
    _name = 'bao.cao.sml.table3'

    week = fields.Integer(string='Tuần')
    product_category_id = fields.Many2one('product.category', string='Danh mục sản phẩm')
    product_category_sub = fields.Char(string='Danh mục sản phẩm', compute='get_product_category_name')
    count_sp_lech = fields.Integer(string='Số mã SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số mã SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')

    @api.multi
    def get_product_category_name(self):
        for rec in self:
            if rec.product_category_id:
                rec.product_category_sub = rec.product_category_id.name
            else:
                rec.product_category_sub = 'Total'


class bao_cao_sml_table4(models.Model):
    _name = 'bao.cao.sml.table4'

    month = fields.Integer(string='Tháng')
    count_sp_lech = fields.Integer(string='Số mã SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số mã SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    count_sp_duy_nhat = fields.Integer(string='SL mã SP duy nhất (tuần)')
    count_sp_active = fields.Integer(string='Số mã đang kinh doanh')
    ty_le_sp = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')


class bao_cao_sml_table5(models.Model):
    _name = 'bao.cao.sml.table5'

    month = fields.Integer(string='Tháng')
    product_category_id = fields.Many2one('product.category', string='Danh mục sản phẩm')
    product_category_sub = fields.Char(string='Danh mục sản phẩm', compute='get_product_category_name')
    count_sp_lech = fields.Integer(string='Số mã SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số mã SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')

    @api.multi
    def get_product_category_name(self):
        for rec in self:
            if rec.product_category_id:
                rec.product_category_sub = rec.product_category_id.name
            else:
                rec.product_category_sub = 'Total'


class bao_cao_sml_table6(models.Model):
    _name = 'bao.cao.sml.table6'

    week = fields.Integer(string='Tuần')
    count_sp_lech = fields.Integer(string='Số lượng SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số lượng SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')


class bao_cao_sml_table7(models.Model):
    _name = 'bao.cao.sml.table7'

    week = fields.Integer(string='Tuần')
    product_category_id = fields.Many2one('product.category', string='Danh mục sản phẩm')
    product_category_sub = fields.Char(string='Danh mục sản phẩm', compute='get_product_category_name')
    count_sp_lech = fields.Integer(string='Số lượng SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số lượng SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')

    @api.multi
    def get_product_category_name(self):
        for rec in self:
            if rec.product_category_id:
                rec.product_category_sub = rec.product_category_id.name
            else:
                rec.product_category_sub = 'Total'


class bao_cao_sml_table8(models.Model):
    _name = 'bao.cao.sml.table8'

    month = fields.Integer(string='Tháng')
    count_sp_lech = fields.Integer(string='Số lượng SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số lượng SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')


class bao_cao_sml_table9(models.Model):
    _name = 'bao.cao.sml.table9'

    month = fields.Integer(string='Tháng')
    product_category_id = fields.Many2one('product.category', string='Danh mục sản phẩm')
    product_category_sub = fields.Char(string='Danh mục sản phẩm', compute='get_product_category_name')
    count_sp_lech = fields.Integer(string='Số lượng SP bị lệch')
    count_sp_kiem = fields.Integer(string='Số lượng SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ (%)', digits=(16, 2))
    bao_cao_kiem_kho_id = fields.Many2one('bao.cao.kiem.kho')

    @api.multi
    def get_product_category_name(self):
        for rec in self:
            if rec.product_category_id:
                rec.product_category_sub = rec.product_category_id.name
            else:
                rec.product_category_sub = 'Total'
