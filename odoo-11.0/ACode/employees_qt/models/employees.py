# -*- coding: utf-8 -*-

from odoo import models, fields, api


class employees_qt(models.Model):
    _inherit = 'hr.employee'

    partner_id = fields.Many2one('res.partner', string='Related Partner', required=1)
    ma_nv = fields.Integer(related='partner_id.id', string='Mã NV')
    dclv_tinh = fields.Char()
    dclv_quan = fields.Char()
    dclv_phuong = fields.Char()
    dclv_thon = fields.Char()
    sdt_cty = fields.Char(related='partner_id.phone', string='Số điện thoại công ty')
    sdt_cn = fields.Char(related='partner_id.mobile', string='Sô điện thoại cá nhân')
    email = fields.Char(related='partner_id.phone', string='Email', required=1)
    notes = fields.Char()

    quoc_tich_id = fields.Many2one('res.country', string='Quốc tịch')
    cmnd = fields.Char(string='CMND')
    ngay_cap = fields.Date(string='Ngày cấp', required=1)
    noi_cap = fields.Char(string='Nơi cấp', required=1)
    dan_toc = fields.Char(string='Dân tộc')
    tgiao = fields.Char(string='Tôn giáo')
    que_quan = fields.Char(string='Quê quán')
    gioi_tinh = fields.Selection([('nu', 'Nữ'), ('nam', 'Nam'), ('khac', 'Giới tính khác')], string="Giới tính")
    dctt_tinh = fields.Char(required=1)
    dctt_quan = fields.Char(required=1)
    dctt_xa = fields.Char(required=1)
    dctt_thon = fields.Char()
    dctr_tinh = fields.Char(required=1)
    dctr_quan = fields.Char(required=1)
    dctr_xa = fields.Char(required=1)
    dctr_thon = fields.Char()
    ngay_sinh = fields.Date(string='Ngày sinh')
    noi_sinh = fields.Char(string='Nơi sinh')
    ngan_hang = fields.Char(string='Ngân hàng', required=1)
    chi_nhanh = fields.Char(string='Chi nhánh', required=1)
    stk = fields.Char(string='Số tài khoản', required=1)
    tinh_trang_hn = fields.Selection([('dt', 'Độc thân'), ('kh', 'Kết hôn'), ('khac', 'Khác')],
                                     string="Tình trạng hôn nhân")
    so_con = fields.Integer(string='Số con')

    tthv = fields.Selection(
        [('thpt', 'Trung học phổ thông'), ('tc', 'Trung cấp'), ('cd', 'Cao đẳng'), ('dh', 'Đại học'),
         ('tdh', 'Trên đại học')], string="Trình độ học vấn", required=1)
    ttccn = fields.Char(string='Tên trường cấp cao nhất')
    cn = fields.Char(string='Chuyên ngành')
    ltn = fields.Char(string='Loại tốt nghiệp')
    nk = fields.Char(string='Niên khóa')
    ttnn = fields.Char(string='Trình độ ngoại ngữ')
    tttt = fields.Char(string='Trình độ tin học')
    bp_id = fields.Many2one('hr.department', string='Bộ phận')
    cd_id = fields.Many2one('hr.job', string='Chức danh')
    qltt = fields.Many2one('hr.employee', string='Quản lý trực tiếp')
    tglv_id = fields.Many2one('resource.calendar', string='Thời gian làm việc')
    tt = fields.Selection([('dlv', 'Đang làm việc'), ('dnv', 'Đã nghỉ việc'), ('dtncv', 'Đang tạm ngưng công việc')],
                          string="Tình trạng")
    hdtv_start = fields.Date()
    hdtv_end = fields.Date()
    hdtv1_start = fields.Date()
    hdtv1_end = fields.Date()
    hdtv2_start = fields.Date()
    hdtv2_end = fields.Date()
    hdldvth = fields.Date(string='HĐLĐ vô thời hạn')
    nnv = fields.Date(string='Ngày nghỉ việc')
