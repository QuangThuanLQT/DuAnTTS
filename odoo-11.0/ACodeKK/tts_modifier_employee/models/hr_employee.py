# -*- coding: utf-8 -*-

from odoo import models, fields, api

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    def get_quoc_tich_vn(self):
        country_vn_id = self.env['res.country'].search([('code', '=', 'VN')],limit=1)
        return country_vn_id.id

    partner_id = fields.Many2one('res.partner', string='Realated Partner', domain=[('is_an_employee', '=', True)], required=1)
    ma_nv = fields.Char(string='Mã NV', compute='get_ma_nv', readonly=1)
    feosco_city_id = fields.Many2one('feosco.city', string='Địa chỉ làm việc', related ='partner_id.feosco_city_id', readonly=1)
    feosco_district_id = fields.Many2one('feosco.district', related='partner_id.feosco_district_id', readonly=1)
    feosco_ward_id = fields.Many2one('feosco.ward', related='partner_id.feosco_ward_id', readonly=1)
    feosco_street = fields.Char(related='partner_id.street', readonly=1)
    sdt_cty = fields.Char(string='Số điện thoại công ty', related='partner_id.phone', readonly=1)
    sdt_canhan = fields.Char(string='Số điện thoại cá nhân', related='partner_id.mobile', readonly=1)
    email = fields.Char(string='Email', related='partner_id.email', readonly=1)

    quoc_tich_id = fields.Many2one('res.country', string="Quốc tịch", default=get_quoc_tich_vn)
    cmnd = fields.Char(string="CMND", required=1)
    ngay_cap = fields.Date(string="Ngày cấp", required = 1)
    noi_cap = fields.Char(string="Nơi cấp", required = 1)
    dan_toc = fields.Char(string="Dân tộc")
    ton_giao = fields.Char(string="Tôn giáo")
    que_quan = fields.Text(string="Quê quán")
    gioi_tinh = fields.Selection([('nam','Nam'),('nu','Nữ'),('khac',"Khác")],string="Giới tính")
    dctt_city_id = fields.Many2one('feosco.city', string='Địa chỉ thường trú',required=1)
    dctt_district_id = fields.Many2one('feosco.district',  required=1, domain="[('city_id', '=', dctt_city_id)]")
    dctt_ward_id = fields.Many2one('feosco.ward', required=1, domain="[('district_id.id', '=', dctt_district_id)]")
    dctt_street = fields.Char()

    dctr_city_id = fields.Many2one('feosco.city', string='Địa chỉ tạm trú',required=1)
    dctr_district_id = fields.Many2one('feosco.district', required=1, domain="[('city_id', '=', dctr_city_id)]")
    dctr_ward_id = fields.Many2one('feosco.ward', required=1, domain="[('district_id.id', '=', dctr_district_id)]")
    dctr_street = fields.Char()
    ngay_sinh = fields.Date(string="Ngày sinh")
    noi_sinh = fields.Char(string="Nơi sinh")
    ngan_hang_id = fields.Many2one('res.partner', domain=[('customer', '=', False),('supplier', '=', False),('bank', '=', True),('company_type', '=', 'company')],string="Ngân hàng",required=1)
    chi_nhanh = fields.Char(string="Chi nhánh",required=1)
    so_tai_khoan = fields.Char(string="Số tài khoản", required=1)
    tt_hn = fields.Selection([('docthan','Độc thân'),('kethon','Kết hôn'),('khac',"Khác")],string="Tình trạng hôn nhân")
    so_con = fields.Integer(string="Số con")
    nguoi_phu_thuoc = fields.Integer(string="Số người phụ thuộc")
    contact_person = fields.Char(string="Liên hệ người thân")
    ma_so_thue_TNCN = fields.Char(string="Mã số Thuế TNCN")

    trinh_do_hoc_van = fields.Selection([('thpt','Trung học phổ thông'),('tc','Trung cấp'),('cd',"Cao đẳng"), ('dh',"Đại học"), ('tdh',"Trên đại học")],string="Trình độ học vấn", required=1)
    ten_truong_cap_cao_nhat = fields.Char(string="Tên trường cấp cao nhất")
    chuyen_nganh = fields.Char(string='Chuyên ngành')
    loai_tot_nghiep = fields.Char(string='Loại tốt nghiệp')
    nien_khoa = fields.Char(string='Niên khóa')
    trinh_do_ngoai_ngu = fields.Char(string='Trình độ ngoại ngữ')
    trinh_do_tin_hoc = fields.Char(string='Trình độ tin học')
    bo_phan_id = fields.Many2one('hr.department', string='Bộ phận')
    chuc_danh_id = fields.Many2one('hr.job', string='Chức danh')
    quan_ly_truc_tiep_id = fields.Many2one('hr.employee', string='Quản lý trực tiếp')
    thoi_gian_lam_viec_id = fields.Many2one('resource.calendar', string='Thời gian làm việc')
    tinh_trang = fields.Selection([('dang_lam_viec','Đang làm việc'),('da_nghi_viec','Đã nghỉ việc'),('da_tam_ngung_cong_viec',"Đã tạm ngưng công việc")],string="Tình trạng")
    hd_thu_viec_start = fields.Date(string="HĐ thử việc", compute='get_hdld')
    hd_thu_viec_end = fields.Date(string="HĐ thử việc", compute='get_hdld')
    hdld_lan_1_start = fields.Date(string="HĐLĐ lần 1", compute='get_hdld')
    hdld_lan_1_end = fields.Date(string="HĐLĐ lần 1", compute='get_hdld')
    hdld_lan_2_start = fields.Date(string="HĐLĐ lần 2", compute='get_hdld')
    hdld_lan_2_end = fields.Date(string="HĐLĐ lần 2", compute='get_hdld')
    hdld_vth = fields.Date(string="HĐLĐ vô thời hạn", compute='get_hdld')
    ngay_nghi_viec = fields.Date(string='Ngày nghỉ việc')

    @api.multi
    @api.onchange('partner_id')
    def get_ma_nv(self):
        for rec in self:
            if rec.partner_id:
                rec.ma_nv = 'NV-%s%s' % (rec.partner_id.employee_company_id.name, rec.partner_id.ma_nv)

    @api.onchange('bo_phan_id')
    def onchange_bo_phan(self):
        if self.bo_phan_id and self.bo_phan_id.manager_id:
            self.quan_ly_truc_tiep_id = self.bo_phan_id.manager_id

    def get_hdld(self):
        for rec in self:
            contract_hdtv = self.env['hr.contract'].search(
                [('type_id', '=', self.env.ref('tts_modifier_employee.contract_type_hdtv').id),('employee_id', '=', rec.id)],limit=1)
            if contract_hdtv:
                rec.hd_thu_viec_start = contract_hdtv.date_start
                rec.hd_thu_viec_end = contract_hdtv.date_end

            contract_hdl1 = self.env['hr.contract'].search(
                [('type_id', '=', self.env.ref('tts_modifier_employee.contract_type_hdl1').id),('employee_id', '=', rec.id)],limit=1)
            if contract_hdl1:
                rec.hdld_lan_1_start = contract_hdl1.date_start
                rec.hdld_lan_1_end = contract_hdl1.date_end

            contract_hdl2 = self.env['hr.contract'].search(
                [('type_id', '=', self.env.ref('tts_modifier_employee.contract_type_hdl2').id),('employee_id', '=', rec.id)],limit=1)
            if contract_hdl2:
                rec.hdld_lan_2_start = contract_hdl2.date_start
                rec.hdld_lan_2_end = contract_hdl2.date_end

            contract_hdvth = self.env['hr.contract'].search(
                [('type_id', '=', self.env.ref('tts_modifier_employee.contract_type_hdvth').id),('employee_id', '=', rec.id)],limit=1)
            if contract_hdvth:
                rec.hdld_vth = contract_hdvth.date_start





