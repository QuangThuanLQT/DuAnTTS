# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class project_inherit(models.Model):
    _inherit = 'project.project'

    state = fields.Selection([
        ('draft', 'Mới'),
        ('quotation', 'Báo giá'),
        ('contract', 'Hợp Đồng'),
        ('manufacturing', 'Sản Xuất'),
        ('delivery', 'Giao Hàng'),
        ('payment', 'Thanh Toán'),
        ('cancel', 'Huỷ'),
    ], 'Status', readonly=True,default='draft')
    revision = fields.Char(string="Rev", default="01")
    job_quotaion_count = fields.Integer(
        compute='_compute_job_quotaion_count'
    )
    record_checked = fields.Boolean('Checked')
    project_code = fields.Char(string="Mã dự án")
    project_value = fields.Float(string='Tài chính')
    label_tasks = fields.Char(default='Nhiệm vụ')
    type_partner = fields.Many2one('project.type.partner',string="Loại khách hàng")
    feature_project = fields.Many2many('feature.project',string="Đặt điểm sản phẩm")
    time_delivery = fields.Selection([
        ('basic','Thông thường'),
        ('quick', 'Nhanh')],'Thời hạn giao hàng')
    partner_sub_id = fields.Many2one('res.partner',string="Khách hàng")
    planning_ids   = fields.One2many('project.planning','project_id',string="Kế hoạch")
    import_data = fields.Binary(string="Tải file của bạn lên")
    import_job_data = fields.Binary(string="Tải file của bạn lên")
    start_date_unit = fields.Selection([
        ('daily','Ngày'),
        ('weekly', 'Tuần')],'Đơn vị')
    guarantee_count = fields.Integer(string='Bảo lãnh',compute='get_guarantee')
    user_email = fields.Char(string="Email")
    user_phone = fields.Char(string="Điện thoại")

    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.user_id:
            self.user_phone = self.user_id.partner_id.mobile or self.user_id.partner_id.phone
            self.user_email = self.user_id.partner_id.email

    @api.multi
    def get_guarantee(self):
        for record in self:
            guarantee_is = record.analytic_account_ids.filtered(lambda ct: ct.is_project == True).mapped('account_guarantee_ids') + self.env['account.guarantee'].search([('project_id','=',record.id)])
            self.guarantee_count = len(guarantee_is)

    @api.multi
    def action_open_guarantee(self):
        guarantee_is = self.analytic_account_ids.filtered(lambda ct: ct.is_project == True).mapped('account_guarantee_ids') + self.env['account.guarantee'].search([('project_id','=',self.id)])
        action = self.env.ref('account_guarantee.account_guarantee_action').read()[0]
        action['domain'] = [('id', 'in', guarantee_is.ids)]
        action['context'] = {'default_project_id':self.id}
        return action

    @api.onchange('partner_sub_id')
    def onchange_partner_sub_id(self):
        for record in self:
            record.partner_id = record.partner_sub_id

    contract_count = fields.Integer(string="Hợp đồng",compute="_get_contract_count")

    def _get_contract_count(self):
        for record in self:
            contract_ids = record.analytic_account_ids.filtered(lambda ct: ct.is_project == True)
            record.contract_count = len(contract_ids)

    @api.multi
    def action_open_contract(self):
        contract_ids = self.analytic_account_ids.filtered(lambda ct: ct.is_project == True)
        action = self.env.ref('stable_account_analytic_analysis.action_account_analytic_overdue_all').read()[0]
        action['domain'] = [('id', 'in', contract_ids.ids)]
        action['context'] = {'default_type': 'contract', 'default_manager_id':self._uid, 'default_is_project': 1, 'default_project_id': self.id}
        return action

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if not self.env.user.has_group('project.group_project_manager'):
            project_list = self.search([('privacy_visibility','!=','followers')]).ids
            project_ids = self.search([('privacy_visibility','=','followers')])
            for project_id in project_ids:
                if self._uid in project_id.mapped('members').ids or self._uid == project_id.user_id.id:
                    project_list.append(project_id.id)
            domain.append(('id','in',project_list))
        res = super(project_inherit, self).search_read(domain=domain, fields=fields, offset=offset,
                                                       limit=limit, order=order)
        return res

    @api.model
    def create(self,vals):
        res = super(project_inherit, self).create(vals)
        res.project_code = self.env['ir.sequence'].next_by_code('project.project.code')
        return res

    @api.multi
    def change_record_checked(self):
        for record in self:
            record.record_checked = not record.record_checked

    @api.multi
    def _compute_job_quotaion_count(self):
        for record in self:
            job_cost = record.mapped('job_cost_ids')
            job_quotaion_ids = self.env['job.quotaion'].search(['|',('job_costing_id','in',job_cost.ids),('project_id','=',record.id)])
            record.job_quotaion_count = len(job_quotaion_ids)


    @api.multi
    def project_to_job_quotaion_action(self):
        job_cost = self.mapped('job_cost_ids')
        job_quotaion_ids = self.env['job.quotaion'].search(
            ['|', ('job_costing_id', 'in', job_cost.ids), ('project_id', '=', self.id)])
        action = self.env.ref('job_quotaion.job_quotaion_action').read()[0]
        action['domain'] = [('id', 'in', job_quotaion_ids.ids)]
        return action

    @api.multi
    def action_quotation(self):
        self.write({'state': 'quotation'})

    @api.multi
    def action_contract(self):
        self.write({'state': 'contract'})

    @api.multi
    def action_manufacturing(self):
        self.write({'state': 'manufacturing'})

    @api.multi
    def action_delivery(self):
        self.write({'state': 'delivery'})

    @api.multi
    def action_payment(self):
        self.write({'state': 'payment'})

    @api.multi
    def button_cancel(self):
        task_type_id = self.env.ref('cptuanhuy_project.project_tuanhuy_type_cancel')
        for task in self.task_ids:
            task.stage_id = task_type_id

        self.write({'state': 'cancel'})

    @api.multi
    def project_report_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        #TODO sumary sheet fomat
        sm_header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'border': 1, })
        sm_header_bold_color_bd_type = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'border': 1})
        sm_header_bold_color_bd_type.set_text_wrap(1)
        sm_header_bold_color_bd_type.set_border(6)
        sm_header_bold_color_right = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'right', 'valign': 'vcenter', 'border': 1, })
        sm_header_bold_color_left = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'border': 1, })

        # TODO have bg_color
        sm_header_bold_color_right_bg = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'right', 'valign': 'vcenter', 'border': 1,
             'bg_color': '#81DAF5', })
        sm_header_bold_color_right_bg.set_border(6)
        sm_header_bold_color_bg = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'bg_color': '#81DAF5', })
        sm_header_bold_color_bg.set_border(6)
        sm_header_bold_color_bg.set_num_format('#,##0')


        sm_body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'border': 1, })
        sm_body_bold_color.set_border(6)
        sm_body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'border': 1, })
        sm_body_bold_color_number.set_num_format('#,##0')
        sm_body_bold_color_number.set_border(6)

        #TODO orther sheet
        header_bold_color_bg_blue = workbook.add_format(
            {'bold': True, 'font_size': '12', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color':'#D5E5FF'})
        header_bold_color_bg_blue.set_text_wrap(1)
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '12', 'align': 'center', 'valign': 'vcenter','border': 1,})
        header_bold_color.set_text_wrap(1)
        header_bold_color_right = workbook.add_format(
            {'bold': True, 'font_size': '12', 'align': 'right', 'valign': 'vcenter','border': 1,})
        header_bold_color_left = workbook.add_format(
            {'bold': True, 'font_size': '12', 'align': 'left', 'valign': 'vcenter','border': 1,})
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'center', 'valign': 'vcenter','border': 1,})
        body_bold_color_number_bg_blue = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color':'#D5E5FF'})
        body_bold_color_number_bg_blue.set_num_format('#,##0')
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'center', 'valign': 'vcenter','border': 1,})
        body_bold_color_number.set_num_format('#,##0')

        job_cost_ids = self.mapped('job_cost_ids')

        #TODO planning sheet

        pl_title_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '18', 'align': 'center', 'valign': 'vcenter', 'border': 1, })
        worksheet = workbook.add_worksheet('PJ planner')
        worksheet.set_column('A:I', 15)
        worksheet.set_row(1, 35)
        worksheet.set_row(0, 35)
        worksheet.merge_range(0, 0, 0, 5, unicode('BẢNG KẾ HOẠCH TRIỂN KHAI DỰ ÁN', "utf-8"), pl_title_bold_color)
        worksheet.write(1, 0, unicode('Hạng mục', "utf-8"), header_bold_color)
        worksheet.write(1, 1, unicode('(Dự kiến)Bắt đầu triển khai', "utf-8"), header_bold_color)
        worksheet.write(1, 2, unicode('(Dự kiến)Thời gian triển khai', "utf-8"), header_bold_color)
        worksheet.write(1, 3, unicode('(Thực tế)Bắt đầu triển khai', "utf-8"), header_bold_color)
        worksheet.write(1, 4, unicode('(Thực tế)Thời gian triển khai', "utf-8"), header_bold_color)
        worksheet.write(1, 5, unicode('Tiến Độ Triển Khai', "utf-8"), header_bold_color)

        row = 1
        for line in self.planning_ids:
            row += 1
            worksheet.write(row, 0, unicode(str(line.name), "utf-8"), body_bold_color)
            worksheet.write(row, 1, line.start_forecast, body_bold_color)
            worksheet.write(row, 2, line.doing_forecast, body_bold_color)
            worksheet.write(row, 3, line.start_actual, body_bold_color)
            worksheet.write(row, 4, line.doing_actual, body_bold_color)
            worksheet.write(row, 5, line.progress, body_bold_color)


        #TODO Sumary sheet
        worksheet = workbook.add_worksheet('Sumary')
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('E:I', 15)
        worksheet.set_column('J:J', 25)
        worksheet.set_row(3,35)

        worksheet.merge_range(0, 1, 0, 9, unicode('BẢNG TỔNG HỢP GIÁ TRỊ DỰ THẦU', "utf-8"), sm_header_bold_color)
        worksheet.write(1, 1, 'CÔNG TRÌNH :', sm_header_bold_color_right)
        worksheet.merge_range(1, 2, 1, 9, unicode(str(self.name), "utf-8"), sm_header_bold_color_left)
        worksheet.write(2, 1, 'Gói Thầu :', sm_header_bold_color_right)
        worksheet.merge_range(2, 2, 2, 9, unicode('', "utf-8"), sm_header_bold_color_left)

        worksheet.write(3, 0, unicode('STT', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 1, unicode('DANH MỤC', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 2, unicode('ĐVT', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 3, unicode('SỐ LƯỢNG', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 4, unicode('VẬT TƯ', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 5, unicode('NHÂN CÔNG', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 6, unicode('Máy Thi Công Vận Chuyển', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 7, unicode('Quản Lý Giám Sát TC', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 8, unicode('TỔNG', "utf-8"), sm_header_bold_color_bd_type)
        worksheet.write(3, 9, unicode('GHI CHÚ', "utf-8"), sm_header_bold_color_bd_type)

        count = 0
        row = 3
        sum_cost_price = sum_labor_cost = sum_manager_cost = sum_move_cost = 0.0
        for job_cost_id in job_cost_ids:
            row += 1
            cost_price = labor_cost = move_cost = manager_cost = 0
            for line in job_cost_id.job_cost_line_ids:
                cost_price = line.cost_price * line.product_qty
                sum_cost_price += cost_price
                labor_cost = line.labor_cost * line.product_qty
                sum_labor_cost += labor_cost
                move_cost = line.move_cost * line.product_qty
                sum_move_cost += move_cost
                manager_cost = line.manager_cost * line.product_qty
                sum_manager_cost += manager_cost
            count += 1
            worksheet.write(row, 0, count, sm_body_bold_color)
            worksheet.write(row, 1, unicode(str(job_cost_id.name),"utf-8"), sm_body_bold_color)
            worksheet.write(row, 2, "HT", sm_body_bold_color)
            worksheet.write(row, 3, "1", sm_body_bold_color)
            worksheet.write(row, 4, cost_price, sm_body_bold_color_number)
            worksheet.write(row, 5, labor_cost, sm_body_bold_color_number)
            worksheet.write(row, 6, move_cost, sm_body_bold_color_number)
            worksheet.write(row, 7, manager_cost, sm_body_bold_color_number)
            worksheet.write(row, 8, cost_price + labor_cost + move_cost + manager_cost, sm_body_bold_color_number)
            worksheet.write(row, 9, "", sm_body_bold_color)
        sum_total = sum_cost_price + sum_labor_cost + sum_move_cost + sum_manager_cost
        row += 1
        worksheet.merge_range(row, 0, row, 3, unicode('TỔNG CỘNG  (CHƯA VAT 10%)', "utf-8"), sm_header_bold_color_right_bg)
        worksheet.write(row, 4, sum_cost_price, sm_header_bold_color_bg)
        worksheet.write(row, 5, sum_labor_cost, sm_header_bold_color_bg)
        worksheet.write(row, 6, sum_move_cost, sm_header_bold_color_bg)
        worksheet.write(row, 7, sum_manager_cost, sm_header_bold_color_bg)
        worksheet.write(row, 8, sum_total, sm_header_bold_color_bg)
        worksheet.write(row, 9, "Tổng Giá Trị Dự Thầu:", sm_header_bold_color_bd_type)
        row += 1
        worksheet.merge_range(row, 0, row, 7, unicode('GIẢM GIÁ %', "utf-8"), sm_header_bold_color_right)
        worksheet.write(row, 8, "%", sm_header_bold_color_bd_type)
        worksheet.write(row, 9, sum_total, sm_body_bold_color_number)


        #TODO orther sheet
        count = 0
        for job_cost_id in job_cost_ids:
            count += 1
            row = 2
            worksheet = workbook.add_worksheet(str(count)+". "+unicode(str(job_cost_id.name), "utf-8"))
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:C', 15)
            worksheet.set_column('F:F', 15)
            worksheet.set_column('G:O', 15)
            worksheet.set_column('P:P', 25)

            worksheet.merge_range(0, 2, 0, 14, unicode('PHỤ LỤC DỰ THẦU', "utf-8"), header_bold_color)
            worksheet.write(1, 1, 'HẠNG MỤC:', header_bold_color)

            worksheet.merge_range(row, 0, row + 2, 0, unicode('STT', "utf-8"), header_bold_color_bg_blue)
            worksheet.merge_range(row, 1, row + 2, 1,unicode('DANH MỤC', "utf-8"),header_bold_color_bg_blue)
            worksheet.merge_range(row, 2, row + 2, 2, unicode('Thương hiệu', "utf-8"), header_bold_color_bg_blue)
            worksheet.merge_range(row, 3, row + 2, 3, unicode('xuất xứ', "utf-8"), header_bold_color_bg_blue)
            worksheet.merge_range(row, 4, row + 2, 4, unicode('ĐVT', "utf-8"), header_bold_color_bg_blue)
            worksheet.merge_range(row, 5, row + 2, 5, unicode('SỐ LƯỢNG', "utf-8"), header_bold_color_bg_blue)

            worksheet.merge_range(row, 6, row, 9, unicode('ĐƠN GIÁ', "utf-8"), header_bold_color_bg_blue)
            worksheet.merge_range(row + 1, 6, row + 2, 6, unicode('VẬT TƯ', "utf-8"), header_bold_color_bg_blue)
            worksheet.merge_range(row + 1, 7, row + 2, 7, unicode('NHÂN CÔNG', "utf-8"), header_bold_color_bg_blue)
            worksheet.merge_range(row + 1, 8, row + 2, 8, unicode('Máy Thi Công Vận Chuyển', "utf-8"), header_bold_color_bg_blue)
            worksheet.merge_range(row + 1, 9, row + 2, 9, unicode('Quản Lý Giám Sát TC', "utf-8"), header_bold_color_bg_blue)

            worksheet.merge_range(row, 10, row, 13, unicode('GIÁ TRỊ', "utf-8"), header_bold_color)
            worksheet.merge_range(row + 1, 10, row + 2, 10, unicode('VẬT TƯ', "utf-8"), header_bold_color)
            worksheet.merge_range(row + 1, 11, row + 2, 11, unicode('NHÂN CÔNG', "utf-8"), header_bold_color)
            worksheet.merge_range(row + 1, 12, row + 2, 12, unicode('Máy Thi Công Vận Chuyển', "utf-8"),header_bold_color)
            worksheet.merge_range(row + 1, 13, row + 2, 13, unicode('Quản Lý Giám Sát TC', "utf-8"), header_bold_color)

            worksheet.merge_range(row, 14, row + 2, 14, unicode('TỔNG', "utf-8"), header_bold_color)
            worksheet.write(row, 15, unicode('GHI CHÚ', "utf-8"), header_bold_color)
            worksheet.merge_range(row + 1, 15, row + 2, 15, unicode('/ Chủng loại hàng hóa', "utf-8"), header_bold_color)
            row += 2
            sum_cost_price = sum_labor_cost = sum_manager_cost = sum_move_cost = sum_total = 0.0
            seq = 0
            for line in job_cost_id.job_cost_line_ids:
                seq += 1
                row += 1
                worksheet.write(row, 0, seq, body_bold_color)
                worksheet.write(row, 1, line.product_id.name,body_bold_color)
                worksheet.write(row, 2, line.product_id.brand_name_select.name or '',body_bold_color)
                worksheet.write(row, 3, line.product_id.source_select.name or '',body_bold_color)
                worksheet.write(row, 4, line.uom_id.name,body_bold_color)
                worksheet.write(row, 5, line.product_qty,body_bold_color)
                worksheet.write(row, 6, line.cost_price,body_bold_color_number)
                worksheet.write(row, 7, line.labor_cost,body_bold_color_number)
                worksheet.write(row, 8, line.move_cost,body_bold_color_number)
                worksheet.write(row, 9, line.manager_cost,body_bold_color_number)
                worksheet.write(row, 10, line.cost_price * line.product_qty,body_bold_color_number)
                worksheet.write(row, 11, line.labor_cost * line.product_qty,body_bold_color_number)
                worksheet.write(row, 12, line.move_cost * line.product_qty,body_bold_color_number)
                worksheet.write(row, 13, line.manager_cost * line.product_qty,body_bold_color_number)
                sum = (line.cost_price + line.labor_cost + line.move_cost + line.manager_cost) * line.product_qty
                worksheet.write(row, 14, sum,body_bold_color_number)
                sum_cost_price += line.cost_price * line.product_qty
                sum_labor_cost += line.labor_cost * line.product_qty
                sum_manager_cost += line.move_cost * line.product_qty
                sum_move_cost += line.manager_cost * line.product_qty
                sum_total += sum

            row += 1
            worksheet.merge_range(row, 7, row, 9, unicode('TỔNG CỘNG  (CHƯA VAT 10%)', "utf-8"),header_bold_color_bg_blue)
            worksheet.write(row, 10, sum_cost_price, body_bold_color_number_bg_blue)
            worksheet.write(row, 11, sum_labor_cost, body_bold_color_number_bg_blue)
            worksheet.write(row, 12, sum_manager_cost, body_bold_color_number_bg_blue)
            worksheet.write(row, 13, sum_move_cost, body_bold_color_number_bg_blue)
            worksheet.write(row, 14, sum_total, body_bold_color_number_bg_blue)
            worksheet.write(row, 15, 'Tổng Giá Trị Dự Thầu:', body_bold_color)
            row += 1
            worksheet.write(row, 13, 'Điều chỉnh %', body_bold_color)
            worksheet.write(row, 14, '0%', body_bold_color)
            worksheet.write(row, 15, sum_total, body_bold_color_number)




        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        date = datetime.now().strftime("%d-%m-%Y")
        name = '[%s]-[%s]-[%s].xlsx'%(self.project_code.split('/')[0] if self.project_code else '',date,self.name)
        attachment_id = attachment_obj.create(
            {'name': name, 'datas_fname': name, 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}


    def clear_all(self):
        if self.planning_ids:
            self.planning_ids.unlink()

    def import_data_excel(self):
        try:
            data = base64.b64decode(self.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            line_ids = self.planning_ids.browse([])
            for row_no in range(sheet.nrows):
                if row_no > 1:
                    row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                               sheet.row(row_no)))
                    if not row[0]:
                        raise UserError('Lỗi format file nhập')
                    else:
                        line_data = {
                            'name': row[0],
                            'start_forecast': int(float(row[1])) if row[1] else 0,
                            'doing_forecast': int(float(row[2])) if row[2] else 0,
                            'start_actual': int(float(row[3])) if row[3] else 0,
                            'doing_actual': int(float(row[4])) if row[4] else 0,
                            'progress': float(row[5]) * 100 if row[5] else 0
                        }
                        line = self.planning_ids.new(line_data)
                        line_ids += line
            self.planning_ids += line_ids
        except:
            raise UserError('Lỗi format file nhập')

    def clear_job_all(self):
        if self.job_cost_ids:
            self.job_cost_ids.unlink()

    def import_job_data_excel(self):
        if not self.partner_id:
            raise UserError('Thiết lập khách hàng cho dự án trước tiên.')
        try:
            data = base64.b64decode(self.import_job_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            line_ids = self.job_cost_ids.browse([])
            for row_no in range(sheet.nrows):
                if row_no > 0:
                    row = (
                    map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                    if not row[0]:
                        raise UserError('Lỗi format file nhập')
                    else:
                        line_data = {
                            'name': row[0],
                            'project_id' : self.id,
                            'analytic_id': self.analytic_account_id.id,
                            'partner_id': self.partner_id.id,
                        }
                        line = self.job_cost_ids.new(line_data)
                        line_ids += line
            self.job_cost_ids += line_ids
        except:
            raise UserError('Lỗi format file nhập')


    def send_email_notification_project(self):
        line = []
        today = datetime.today().date()
        today_str = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        project_ids = self.search([('date_start', '<=', today_str)])

        for project in project_ids:
            email_teplate = self.env.ref('cptuanhuy_project.project_notification')
            email_teplate.send_mail(project.id, force_send=True, raise_exception=True)








class project_type_partner(models.Model):
    _name = 'project.type.partner'

    name = fields.Char(string='Loại')

class feature_project(models.Model):
    _name = 'feature.project'

    name = fields.Char(string='Loại')