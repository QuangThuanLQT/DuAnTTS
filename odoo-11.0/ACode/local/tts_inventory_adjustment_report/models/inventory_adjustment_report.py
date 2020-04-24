# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta, MO
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class inventory_adjustment_report(models.Model):
    _name = 'inventory.adjustment.report'

    type_report = fields.Selection(
        [('so_ma_lech', 'Báo cáo số mã lệch'), ('so_luong_lech', 'Báo cáo số lượng lệch'), ('all', 'Cả hai')],
        default='so_ma_lech', string='Loại báo cáo')
    type_time = fields.Selection([('tuan', 'Tuần'), ('thang', 'Tháng')], default='tuan', string='Loại thời gian')
    start_date = fields.Date(string='Từ Ngày')
    end_date = fields.Date(string='Đến Ngày')
    check_product_day_ids = fields.One2many('check.product.day','adjustment_report_id')



class check_product_day(models.Model):
    _name = 'check.product.day'

    date = fields.Date(string='Ngày')
    so_ma_lech = fields.Integer(string='Số mã SP bị lệch')
    so_ma_kiem = fields.Integer(string='Số mã SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ(%)')
    adjustment_report_id = fields.Many2one('inventory.adjustment.report')

class check_product_week(models.Model):
    _name = 'check.product.week'

    weekly = fields.Integer(string='Tuần')
    so_ma_lech = fields.Integer(string='Số mã SP bị lệch')
    so_ma_kiem = fields.Integer(string='Số mã SP kiểm')
    ty_le = fields.Float(string='Tỉ lệ(%)')
    so_ma_duy_nhat = fields.Integer(string='SL mã duy nhất(tuần)')
    so_ma_dang_kinh_doanh = fields.Integer(string='Số mã đang kinh doanh')
    ty_le_ma_duy_nhat = fields.Float(string='Tỉ lệ(%)')

class check_product_by_category_week(models.Model):
    _name = 'check.product.by.category.week'

    weekly = fields.Integer(string='Tuần')
    so_ma_lech = fields.Integer(string='Số mã SP bị lệch')
    total = fields.Integer(string='')
    bong_da = fields.Integer(string='')
    bong_ro = fields.Integer(string='')
    cau_long = fields.Integer(string='')
    gym_sportwear = fields.Integer(string='')

