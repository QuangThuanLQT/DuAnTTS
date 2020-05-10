# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, SUPERUSER_ID, tools
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook
from odoo.exceptions import UserError


class job_costing_fail(models.TransientModel):
    _name = 'job.costing.fail'

    reason = fields.Char('Lý do', required=True)

    @api.multi
    def action_confirm(self):
        if 'active_id' in self._context and self._context['active_id']:
            job_costing_id = self.env['job.costing'].browse(self._context['active_id'])
            if job_costing_id:
                job_costing_id.action_fail(self.reason)


class job_quotaion_cost(models.Model):
    _name = 'job.quotaion.cost'

    job_costing_id = fields.Many2one('job.costing')
    job_quotaion_id = fields.Many2one('job.quotaion', 'Định mức')
    job_quotaion_code = fields.Char("Mã định mức", readonly=True, related='job_quotaion_id.job_quotaion_code')
    state = fields.Selection([
        ('draft', 'Bản nháp'),
        ('done', 'Hoàn thành'),
    ], 'Status', default='draft', readonly=True, related='job_quotaion_id.state')
    total_cost = fields.Float('Tổng phụ', compute='get_total_cost',store=True)
    type       = fields.Many2one('job.quotaion.type', string='Loại')
    quantity = fields.Float('Số lượng',default=1)

    @api.multi
    def open_update_price_job_costing(self):
        action = self.env.ref('cptuanhuy_project.update_price_job_costing_action_base_jq').read()[0]
        action['context'] = {'job_costing_id': self.job_costing_id.id, 'job_quotaion_id': self.job_quotaion_id.id}
        return action

    @api.depends('job_costing_id', 'job_quotaion_id')
    def get_total_cost(self):
        for record in self:
            total = 0
            if record.job_costing_id and record.job_quotaion_id:
                ids = record.job_costing_id.job_cost_line_ids.filtered(lambda job_cost: job_cost.job_quotation_id == record.job_quotaion_id)
                for line in ids:
                    total += line.total_cost
            record.total_cost = total

    @api.onchange('job_quotaion_id')
    def onchange_job_quotaion_id(self):
        self.type = self.job_quotaion_id.type


class job_costing_inherit(models.Model):
    _inherit = 'job.costing'

    @api.depends(
        'child_job_costing_ids',
        'child_job_costing_ids.child_job_costing_id',
        'child_job_costing_ids.quantity',
        'job_cost_line_ids',
        'job_cost_line_ids.product_qty',
        'job_cost_line_ids.cost_price',
        'job_cost_line_ids.labor_cost',
        'job_cost_line_ids.move_cost',
        'job_cost_line_ids.manager_cost',
    )
    def _compute_material_total(self):
        for rec in self:
            rec.material_total = sum(
                [(p.product_qty * (p.cost_price + p.labor_cost + p.move_cost + p.manager_cost)) for p in
                 rec.job_cost_line_ids])
            rec.material_total += sum(
                [(p.sub_total) for p in
                 rec.child_job_costing_ids])

    reason                = fields.Char('Lý do', readonly=True)
    state                 = fields.Selection(selection_add=[('fail', 'Không đạt')])
    sum_total_expected    = fields.Float(
        string='Tổng giá vốn dự kiến',
        compute='_compute_total_expected',
        store=True,
    )
    profit_gross          = fields.Char(
        string='Lợi nhuận gộp',
        compute='_compute_total_expected',
        store=True,
    )

    labor_cost_percent    = fields.Float(string='Đơn giá nhân công (%)')
    move_cost_percent     = fields.Float(string='Máy Thi Công Vận Chuyển (%)')
    manager_cost_percent  = fields.Float(string='Quản Lý Giám Sát TC (%)')
    job_quotation_ids     = fields.Many2many('job.quotaion', string='Định mức')
    child_job_costing_ids = fields.One2many('child.job.costing', 'parent_job_costing_id', string="Báo giá con")
    discount_type         = fields.Selection([
        ('percent', 'Theo phầm trăm'),
        ('amount', 'Theo giá')
    ], defult='percent', string='Loại giảm giá')
    discount              = fields.Float(string="Mức giảm")
    total_discount        = fields.Float(compute='_get_total_discount', string='Giảm giá tổng', store=True)
    import_data           = fields.Binary(string="Tải file của bạn lên")
    total_tax             = fields.Float(string="Tổng thuế", compute='get_total_tax', store=True)
    total_after_tax       = fields.Float(string='Tổng giá trị báo giá sau thuế', compute='get_total_after_tax', store=True)
    job_quotaion_cost_ids = fields.One2many('job.quotaion.cost', 'job_costing_id')
    so_count              = fields.Integer(string='Đơn hàng', compute='get_so_count')

    @api.model
    def create(self, values):
        result = super(job_costing_inherit, self).create(values)
        for line in result.job_quotaion_cost_ids:
            if line.type != line.job_quotaion_id.type:
                line.job_quotaion_id.type = line.type
                line.job_quotaion_id.action_confirm()
                # if line.job_quotaion_id.bom_id:
                #     if line.type == self.env.ref('cptuanhuy_project.job_quotaion_type_manufacturing'):
                #         line.job_quotaion_id.bom_id.type = 'normal'
                #     else:
                #         line.job_quotaion_id.bom_id.type = 'phantom'
        return result

    @api.multi
    def write(self, values):
        result = super(job_costing_inherit, self).write(values)
        for rec in self:
            for line in rec.job_quotaion_cost_ids:
                if line.type != line.job_quotaion_id.type:
                    line.job_quotaion_id.type = line.type
                    line.job_quotaion_id.action_confirm()
                    # if line.job_quotaion_id.bom_id:
                    #     if line.type == self.env.ref('cptuanhuy_project.job_quotaion_type_manufacturing'):
                    #         line.job_quotaion_id.bom_id.type = 'normal'
                    #     else:
                    #         line.job_quotaion_id.bom_id.type = 'phantom'
        return result

    @api.multi
    def get_so_count(self):
        for record in self:
            sale_orders = self.env['sale.order'].search([
                ('job_costing_id', '=', record.id),
                ('state', '!=', 'cancel')
            ])
            record.so_count = len(sale_orders._ids)

    @api.depends('job_cost_line_ids.total_cost','job_cost_line_ids.tax')
    def get_total_tax(self):
        for rec in self:
            tax = 0
            for line in rec.job_cost_line_ids:
                if line.tax and line.tax != 0:
                    tax += line.total_cost * line.tax / 100
            rec.total_tax = int(tax)

    @api.depends('total_tax', 'jobcost_total')
    def get_total_after_tax(self):
        for rec in self:
            rec.total_after_tax = rec.jobcost_total + rec.total_tax

    def import_data_excel(self):
        try:
            data = base64.b64decode(self.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            # line_ids = self.job_cost_line_ids.browse([])
            for row_no in range(sheet.nrows):
                if row_no > 0:
                    row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                               sheet.row(row_no)))
                    # job_type_id = self.env['job.type'].search([('name','=',row[0].strip())],limit=1)
                    # if not job_type_id and row[0] != "":
                    #     job_type_id = self.env['job.type'].create({
                    #         'name' : row[0].strip(),
                    #         'code' : row[0].strip(),
                    #         'jop_type' : 'material',
                    #     })
                    if row[0].strip() or row[0].strip() != '':
                        product_id = self.env['product.product'].search([('default_code','=',row[0].strip())])
                        if not product_id:
                            product_data = {
                                'name': row[1].strip(),
                                'default_code': row[0].strip(),
                            }
                            if row[2].strip():
                                product_uom_id = self.env['product.uom'].search([('name','=',row[2].strip())])
                                if product_uom_id:
                                    product_data.update({
                                        'uom_id' : product_uom_id.id,
                                        'uom_po_id': product_uom_id.id,
                                    })
                            product_id  = self.env['product.product'].create(product_data)
                        line_context = {
                            'partner_id': self.partner_id.id,
                            'default_analytic_id': self.analytic_id,
                            'labor_cost_percent': self.labor_cost_percent,
                            'manager_cost_percent': self.manager_cost_percent,
                            'move_cost_percent': self.move_cost_percent,
                        }
                        line_data = self.job_cost_line_ids.with_context(line_context).default_get(self.job_cost_line_ids._fields)
                        line_data.update({
                            'product_id'  : product_id.id,
                            'product_qty' : row[3].strip() and float(row[3].strip()) or 0,
                            'job_type' : 'material',
                        })
                        line = self.job_cost_line_ids.with_context(line_context).create(line_data)
                        line._onchange_product_id()
                        line.onchange_product_for_ck()
                        if row[4] or row[4] != 0:
                            line.price_discount = float(row[4])
                        self.job_cost_line_ids += line
        except:
            raise UserError('Lỗi format file nhập')

    def export_data_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Vat lieu cua bao gia [%s] - %s' % (self.number,self.name))

        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 5)
        worksheet.set_column('E:E', 5)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:K', 15)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 15)
        worksheet.set_column('N:N', 15)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['Hạng mục', 'Mã sản phẩm', 'Sản phẩm','SL','ĐVT', 'Chi phí / Đơn vị', 'Đơn Giá','Đơn giá nhân công',
                          'Máy Thi Công Vận Chuyển','Quản Lý Giám Sát TC','Chiết khấu','Giá trực tiếp','Chi phí dự kiến','Tổng phụ']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for line in self.job_cost_line_ids:
            row += 1
            worksheet.write(row, 0, line.job_type_id.name if line.job_type_id else '', body_bold_color)
            worksheet.write(row, 1, line.product_id.default_code, body_bold_color)
            worksheet.write(row, 2, line.product_id.name, body_bold_color)
            worksheet.write(row, 3, line.product_qty, body_bold_color_number)
            worksheet.write(row, 4, line.uom_id.name, body_bold_color)
            worksheet.write(row, 5, line.price_ihr, body_bold_color_number)
            worksheet.write(row, 6, line.cost_price, body_bold_color_number)
            worksheet.write(row, 7, line.labor_cost, body_bold_color_number)
            worksheet.write(row, 8, line.move_cost, body_bold_color_number)
            worksheet.write(row, 9, line.manager_cost, body_bold_color_number)
            worksheet.write(row, 10, line.discount, body_bold_color_number)
            worksheet.write(row, 11, line.price_discount, body_bold_color_number)
            worksheet.write(row, 12, line.verage_cost, body_bold_color_number)
            worksheet.write(row, 13, line.total_cost, body_bold_color_number)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'vat_lieu.xlsx',
            'datas_fname': 'vat_lieu.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }


    @api.depends(
        'material_total',
        'labor_total',
        'overhead_total',
        'discount_type',
        'discount'
    )
    def _get_total_discount(self):
        for rec in self:
            total_discount = rec.material_total + rec.labor_total + rec.overhead_total
            if rec.discount_type == 'amount':
                total_discount = rec.discount
            elif rec.discount_type == 'percent':
                total_discount = total_discount * rec.discount / 100
            else:
                total_discount = 0
            rec.total_discount = total_discount

    @api.multi
    def update_job_costing(self):
        for record in self:
            for line in record.job_cost_line_ids:
                if line.price_discount:
                    continue
                line.onchange_product_for_ck(self.partner_id.id)
                line.onchange_price_ihr()
                line._compute_total_cost()
            for line in record.child_job_costing_ids:
                line.onchange_child_job_costing()
            record.onchange_compute_total_cost()
            record._compute_total_expected()
            record._compute_material_total()


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.search(args)
        if name:
            recs = self.search(['|',('name', '=', name),('number', 'ilike', name)] + args, limit=limit)
        return recs.name_get()

    @api.onchange('project_id')
    def onchange_project_id(self):
        for rec in self:
            rec.partner_id = rec.project_id.partner_id.id
        return

    @api.onchange('labor_cost_percent', 'move_cost_percent', 'manager_cost_percent')
    def onchange_compute_total_cost(self):
        for record in self:
            for line in record.job_cost_line_ids:
                if self.labor_cost_percent > 0:
                    line.labor_cost = line.price_ihr * record.labor_cost_percent * (10 ** -2)
                else:
                    line.labor_cost = line.product_id.labor_cost or 0
                if self.move_cost_percent > 0:
                    line.move_cost = line.price_ihr * record.move_cost_percent * (10 ** -2)
                else:
                    line.move_cost = 0
                if self.manager_cost_percent > 0:
                    line.manager_cost = line.price_ihr * record.manager_cost_percent * (10 ** -2)
                else:
                    line.manager_cost = 0

                # line.with_context(partner_id=self.partner_id and self.partner_id.id or False).onchange_product_for_ck(self.partner_id.id,self.labor_cost_percent, self.move_cost_percent, self.manager_cost_percent)

    @api.depends('job_labour_line_ids.product_qty', 'job_labour_line_ids.product_id', 'material_total','total_discount')
    def _compute_total_expected(self):
        for rec in self:
            sum_total_expected = sum([(line.verage_cost * line.product_qty) for line in rec.job_cost_line_ids])
            sum_total_expected += sum([(line.verage_cost * line.quantity) for line in rec.child_job_costing_ids])
            sum_total_expected = sum_total_expected - rec.total_discount
            rec.sum_total_expected = sum_total_expected
            profit_gross = rec.material_total - sum_total_expected
            profit_gross_percent = 0
            if rec.material_total != 0:
                profit_gross_percent = round((profit_gross / rec.material_total * 100),2)
            rec.profit_gross = "%sđ (%s" % ('{0:,.2f}'.format(profit_gross),profit_gross_percent) + '%)'

    @api.multi
    def action_fail(self, reason):
        self.write({
            'reason': reason,
            'state': 'fail'
        })

    @api.multi
    def button_fail(self):
        return {
            'name': 'Báo giá không đạt',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'job.costing.fail',
            'target': 'new',
        }


    @api.multi
    def confirm_job_quotation(self):
        for record in self:
            for job_quotation in record.job_quotaion_cost_ids:
                if job_quotation.job_quotaion_id.state == 'draft':
                    raise UserError("Định mức '%s' cần xác nhận."%(job_quotation.job_quotaion_id.name))
            list_unlink = []
            for i in range(0,len(record.job_quotaion_cost_ids)):
                for j in range(i+1,len(record.job_quotaion_cost_ids)):
                    if record.job_quotaion_cost_ids[i].job_quotaion_id == record.job_quotaion_cost_ids[j].job_quotaion_id:
                        record.job_quotaion_cost_ids[i].quantity += record.job_quotaion_cost_ids[j].quantity
                        list_unlink.append(record.job_quotaion_cost_ids[j])
            for rec in list_unlink:
                rec.unlink()

            record.job_cost_line_ids.filtered(lambda l:l.job_quotation_id).unlink()
            for job_quotation in record.job_quotaion_cost_ids:
                if job_quotation.job_quotaion_id:
                    for line in job_quotation.job_quotaion_id.line_ids:
                        data = {}
                        if line.product_id:
                            data.update({
                                'date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
                                'job_type': 'material',
                                'product_id': line.product_id.id,
                                'description': line.product_id.name,
                                'product_qty': float(line.so_luong) * job_quotation.quantity,
                                'uom_id': line.product_id.uom_id.id,
                                'job_quotation_id': job_quotation.job_quotaion_id.id,
                                'job_quotation_line_id' : line.id,
                            })

                            line = record.job_cost_line_ids.new(data)
                            line._onchange_product_id()
                            line.onchange_product_for_ck(record.partner_id.id)
                            line.onchange_price_ihr()
                            record.job_cost_line_ids += line
                job_quotation.get_total_cost()
        True

    @api.multi
    def update_job_quation(self):
        for record in self.search([]):
            for job_quotation_id in record.job_quotation_ids:
                job_quotaion_cost_id = self.env['job.quotaion.cost'].search([('job_quotaion_id', '=', job_quotation_id.id), ('job_costing_id', '=', record.id)], limit=1)
                if not job_quotaion_cost_id:
                    job_quotaion_cost_id = self.env['job.quotaion.cost'].create({
                        'job_costing_id': record.id,
                        'job_quotaion_id': job_quotation_id.id
                    })

    @api.multi
    def job_costing_create_product(self):
        for rec in self:
            product_id = self.env['product.template'].search([('default_code', '=', rec.number)])
            line_not_jq = self.job_cost_line_ids.filtered(lambda l: not l.job_quotation_id)
            if not product_id:
                if line_not_jq:
                    product_id = self.env['product.template'].create({
                        'name': rec.name,
                        'default_code': rec.number,
                        'list_price': sum(line_not_jq.mapped('total_cost')),
                        'standard_price': sum(line_not_jq.mapped('total_cost')),
                        'type': 'product',
                    })

                    bom_data = {
                        'product_tmpl_id': product_id.id,
                        'product_qty': 1,
                        'product_uom_id': product_id.uom_id.id,
                        'type': 'phantom',
                        'bom_line_ids': [(0, 0, {
                            'product_id': line.product_id.id,
                            'product_qty': line.product_qty,
                            'product_uom_id': line.uom_id.id or line.product_id.uom_id.id

                        }) for line in line_not_jq]

                    }
                    self.env['mrp.bom'].create(bom_data)
            else:
                product_id.write({
                    'name': rec.name,
                    'list_price': sum(line_not_jq.mapped('total_cost')),
                    'standard_price': sum(line_not_jq.mapped('total_cost')),
                })
                bom_ids = self.env['mrp.bom'].search([('product_tmpl_id','=',product_id.id)])
                for bom_id in bom_ids:
                    bom_id.bom_line_ids.unlink()
                    if line_not_jq:
                        bom_id.write({
                            'bom_line_ids': [(0, 0, {
                                'product_id': line.product_id.id,
                                'product_qty': line.product_qty,
                                'product_uom_id': line.uom_id.id or line.product_id.uom_id.id
                            }) for line in line_not_jq]
                        })

    @api.multi
    def action_confirm(self):
        for rec in self:
            if 'continue_confirm' not in self._context:
                job_quotaion_ids = self.env['job.quotaion']
                for job_quotaion_cost_id in rec.job_quotaion_cost_ids:
                    job_quotaion = job_quotaion_cost_id.job_quotaion_id
                    jc_same_jb_ids = rec.job_cost_line_ids.filtered(lambda l: l.job_quotation_id == job_quotaion)
                    if len(jc_same_jb_ids) != len(job_quotaion.line_ids):
                        job_quotaion_ids += job_quotaion
                        continue
                    for jc_line in jc_same_jb_ids:
                        if jc_line.product_id != jc_line.job_quotation_line_id.product_id or jc_line.product_qty != float(jc_line.job_quotation_line_id.so_luong) * job_quotaion_cost_id.quantity:
                            job_quotaion_ids += job_quotaion
                            break
                if job_quotaion_ids:
                    name = "Linh kiện trong báo giá khác với các định mức ban đầu: " + ", ".join(job_quotaion_ids.mapped('name'))
                    action = self.env.ref('cptuanhuy_project.warning_confirm_job_costing_action').read()[0]
                    action['context'] = {'name': name, 'job_costing_id': rec.id, 'job_quotaion_ids' : job_quotaion_ids.ids }
                    return action
                    break
                else:
                    rec.job_costing_create_product()
                    rec.write({
                        'state': 'confirm',
                    })
            else:
                rec.job_costing_create_product()
                rec.write({
                    'state': 'confirm',
                })
            if rec.child_job_costing_ids:
                rec.child_job_costing_ids.mapped('child_job_costing_id').action_confirm()

    @api.multi
    def open_update_price_job_costing(self):
        action = self.env.ref('cptuanhuy_project.update_price_job_costing_action_1').read()[0]
        action['context'] = {'job_costing_id': self.id}
        return action

class job_cost_line_inherit(models.Model):
    _inherit = 'job.cost.line'

    price_ihr = fields.Float(string="Chi phí / Đơn vị")
    discount = fields.Float(string="Chiết khấu")
    price_discount = fields.Float(string="Giá trực tiếp")
    labor_cost = fields.Float(string="Đơn giá nhân công")
    verage_cost = fields.Float(string="Chi phí dự kiến")
    move_cost = fields.Float(string="Máy Thi Công Vận Chuyển")
    manager_cost = fields.Float(string="Quản Lý Giám Sát TC")
    list_price = fields.Float(string="Giá bán")
    tax = fields.Integer(string="Thuế")
    job_quotation_id = fields.Many2one('job.quotaion', 'Định mức')
    job_quotation_line_id = fields.Many2one('job.quotaion.line')

    @api.multi
    def open_update_price_job_costing(self):
        action = self.env.ref('cptuanhuy_project.update_price_job_costing_action').read()[0]
        action['context'] = {'job_costing_line': self.id}
        return action

    @api.onchange('tax')
    def onchange_tax(self):
        if self.tax not in (0,5,10):
            self.tax = 0

    @api.model
    def default_get(self, fields):
        res = super(job_cost_line_inherit, self).default_get(fields)
        res['date'] = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        return res

    @api.depends('product_qty', 'hours', 'cost_price', 'direct_id', 'labor_cost', 'move_cost', 'manager_cost')
    def _compute_total_cost(self):
        for rec in self:
            # labor_cost_percent = manager_cost_percent = move_cost_percent = 0.0
            # if rec.direct_id and rec.direct_id.labor_cost_percent:
            #     labor_cost_percent = rec.direct_id.labor_cost_percent
            # if rec.direct_id and rec.direct_id.manager_cost_percent:
            #     manager_cost_percent = rec.direct_id.manager_cost_percent
            # if rec.direct_id and rec.direct_id.move_cost_percent:
            #     move_cost_percent = rec.direct_id.move_cost_percent
            # if rec.job_type == 'labour':
            #     rec.product_qty = 0.0
            #     rec.total_cost = rec.hours * rec.cost_price + rec.product_qty * (rec.labor_cost + rec.move_cost + rec.manager_cost)
            # else:
            #     rec.hours = 0.0
            rec.total_cost = rec.product_qty * (rec.cost_price + rec.labor_cost + rec.move_cost + rec.manager_cost)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.description = rec.product_id.name
            if not rec.product_qty:
                rec.product_qty = 1.0
            rec.labor_cost = rec.product_id.labor_cost or 0
            rec.uom_id = rec.product_id.uom_id
            rec.verage_cost = rec.product_id.standard_price
            rec.list_price = rec.product_id.list_price
            rec.tax = rec.product_id.taxes_id[0].amount if rec.product_id.taxes_id else 0


    @api.onchange('price_ihr', 'price_discount', 'discount')
    def onchange_price_ihr(self):
        for record in self:
            record.cost_price = record.price_discount or record.price_ihr * (1 - record.discount / 100)

    @api.multi
    @api.onchange('product_id')
    def onchange_product_for_ck(self, partner=None, labor_cost_percent=None, move_cost_percent=None, manager_cost_percent=None):
        for record in self:
            record.price_ihr = record.product_id.lst_price
            record.discount = 0
            record.price_discount = 0
            if record.product_id and record.product_id.product_tmpl_id and (
                            'partner_id' in self._context and  self._context.get('partner_id',False) or partner):
                group_sale_id = record.product_id.product_tmpl_id.group_sale_id
                if 'partner_id' in self._context:
                    partner_id = self.env['res.partner'].search([('id', '=', self._context.get('partner_id'))])
                elif partner:
                    partner_id = self.env['res.partner'].search([('id', '=', partner)])
                if group_sale_id:
                    if not group_sale_id.price_type or group_sale_id.price_type == 'list_price':
                        discount = group_sale_id.group_line_ids.filtered(
                            lambda x: x.partner_id == partner_id or x.partner_name.upper() in partner_id.name.upper() if x.partner_name else False)
                        if discount:
                            record.discount = discount[0].discount
                        else:
                            string = unicode("Ngoài những khách hàng đã lk", "utf-8")
                            discount = group_sale_id.group_line_ids.filtered(
                                lambda x: x.partner_name == string) and group_sale_id.group_line_ids.filtered(
                                lambda x: x.partner_name == string).discount or group_sale_id.group_line_ids and \
                                                                                group_sale_id.group_line_ids[
                                                                                    0].discount or 0
                            record.discount = discount
                        record.price_ihr = record.product_id.lst_price

                    else:
                        discount = group_sale_id.group_line_ids.filtered(
                            lambda x: x.partner_id == partner_id or x.partner_name.upper() in partner_id.name.upper() if x.partner_name else False)
                        price_unit = sum(record.product_id.mapped(group_sale_id.price_type))
                        if discount:
                            record.price_ihr = price_unit
                            record.discount = -discount[0].discount
                        else:
                            string = unicode("Ngoài những khách hàng đã lk", "utf-8")
                            discount = group_sale_id.group_line_ids.filtered(
                                lambda x: x.partner_name == string) and group_sale_id.group_line_ids.filtered(
                                lambda x: x.partner_name == string).discount or group_sale_id.group_line_ids and \
                                                                                group_sale_id.group_line_ids[
                                                                                    0].discount or 0
                            record.price_ihr = price_unit
                            record.discount = -discount

            if 'labor_cost_percent' in record._context and record._context['labor_cost_percent'] and record._context['labor_cost_percent'] > 0:
                record.labor_cost = record.price_ihr * record._context['labor_cost_percent'] * (10 ** -2)
            else:
                record.labor_cost = record.product_id.labor_cost
            if 'move_cost_percent' in record._context and self._context['move_cost_percent'] and record._context['move_cost_percent'] > 0:
                record.move_cost = record.price_ihr * record._context['move_cost_percent'] * (10 ** -2)
            else:
                record.move_cost = 0
            if 'manager_cost_percent' in record._context and record._context['manager_cost_percent'] and record._context['manager_cost_percent'] > 0:
                record.manager_cost = record.price_ihr * record._context['manager_cost_percent'] * (10 ** -2)
            else:
                record.manager_cost = 0

class warning_confirm_job_costing(models.TransientModel):
    _name = 'warning.confirm.job.costing'

    name = fields.Text(readonly=1)
    job_costing_id = fields.Many2one('job.costing')
    job_quotaion_ids = fields.Many2many('job.quotaion')

    @api.model
    def default_get(self, fields):
        res = super(warning_confirm_job_costing, self).default_get(fields)
        if self._context and 'name' in self._context:
            res['name'] = self._context.get('name', False)
        if self._context and 'job_costing_id' in self._context:
            res['job_costing_id'] = self._context.get('job_costing_id', False)
        if self._context and 'job_quotaion_ids' in self._context:
            res['job_quotaion_ids'] = [(6,0,self._context.get('job_quotaion_ids', False))]
        return res

    @api.multi
    def update_job_quotaion(self):
        for rec in self:
            for job_quotaion in rec.job_quotaion_ids:
                jc_same_jb_ids = rec.job_costing_id.job_cost_line_ids.filtered(lambda l: l.job_quotation_id == job_quotaion)
                job_quotaion_cost = rec.job_costing_id.job_quotaion_cost_ids.filtered(lambda l: l.job_quotaion_id == job_quotaion)
                job_quotaion_line = self.env['job.quotaion.line']
                for jc_line in jc_same_jb_ids:
                    if jc_line.job_quotation_line_id:
                        job_quotaion_line += jc_line.job_quotation_line_id
                        if jc_line.product_id != jc_line.job_quotation_line_id.product_id:
                            jc_line.job_quotation_line_id.product_id = jc_line.product_id
                        if jc_line.product_qty != float(jc_line.job_quotation_line_id.so_luong) * job_quotaion_cost.quantity:
                            jc_line.job_quotation_line_id.so_luong = jc_line.product_qty / job_quotaion_cost.quantity
                    else:
                        line = job_quotaion.line_ids.create({
                            'product_id' : jc_line.product_id.id,
                            'so_luong': jc_line.product_qty / job_quotaion_cost.quantity,
                            'product_uom' : jc_line.product_id.uom_id.id,
                        })
                        job_quotaion.line_ids += line
                        jc_line.job_quotation_line_id = line
                        job_quotaion_line += line

                job_quotaion_line_residual = job_quotaion.line_ids - job_quotaion_line
                job_quotaion_line_residual.unlink()
                job_quotaion.action_confirm()
                job_quotaion.product_id.list_price = sum(jc_same_jb_ids.mapped('total_cost'))

    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.job_costing_id.with_context(continue_confirm = True).action_confirm()

