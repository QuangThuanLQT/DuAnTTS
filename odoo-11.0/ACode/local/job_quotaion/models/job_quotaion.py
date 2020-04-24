# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from xlrd import open_workbook
import json
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import base64
import StringIO
import xlsxwriter

class job_quotaion(models.Model):
    _name = 'job.quotaion'
    _inherit = 'mail.thread'

    name = fields.Char('Tên')
    line_ids = fields.One2many('job.quotaion.line','job_quotaion_id')
    import_data = fields.Binary(string="Tải file của bạn lên")
    state = fields.Selection([
        ('draft', 'Bản nháp'),
        ('done', 'Hoàn thành'),
    ], 'Status', default='draft',readonly=True)
    # project_id = fields.Many2one('project.project',string="Dự án")
    # partner_id = fields.Many2one('res.partner',string="Khách hàng",required=False)
    date = fields.Date(string="Ngày tạo",default=fields.Date.context_today)
    job_costing_id = fields.Many2one('job.costing')
    job_costing_count = fields.Integer(compute="_get_job_costing_count")
    job_quotaion_code = fields.Char("Mã định mức",readonly=True)
    is_sample = fields.Boolean('Định mức mẫu')
    job_quotaion_sample = fields.Many2many('job.quotaion', 'job_quotaion_sample_rel', 'job_quotaion_id', 'job_quotaion_sample_id', domain=[('is_sample', '=', True)], string='Định mức mẫu')


    @api.onchange('job_quotaion_sample')
    def onchange_job_quotaion_sample(self):
        if self.job_quotaion_sample:
            data = self.line_ids.filtered(lambda r: not r.job_quotaion_sample)
            self.line_ids = None
            line_ids = self.line_ids.browse([])
            for job_quotaion in self.job_quotaion_sample:
                for line in job_quotaion.line_ids:
                    line_data = {
                        'type': line.type and line.type.id or False,
                        'description': line.description,
                        'key_word': line.key_word,
                        'nha_san_xuat': line.nha_san_xuat,
                        'ma_san_pham': line.ma_san_pham,
                        'xuat_su': line.xuat_su,
                        'product_uom': line.product_uom and line.product_uom.id or False,
                        'so_luong': line.so_luong,
                        'note': line.note,
                        'ma_dat_hang': line.ma_dat_hang,
                        'product_id_deff': line.product_id_deff and line.product_id_deff.id or False,
                        'product_ids': line.product_ids,
                        'product_id': line.product_id and line.product_id.id or False,
                        'job_quotaion_sample': job_quotaion.id or False,
                    }
                    record = self.line_ids.new(line_data)
                    # record.onchange_product_id()
                    line_ids += record
            self.line_ids += line_ids
            self.line_ids += data
        else:
            data = self.line_ids.filtered(lambda r: not r.job_quotaion_sample)
            self.line_ids = None
            self.line_ids = data

    def _get_job_costing_count(self):
        for record in self:
            record.job_costing_count = len(record.job_costing_id)

    @api.multi
    def open_job_costing(self):
        job_cost = self.mapped('job_costing_id')
        if len(job_cost) != 1:
            action = self.env.ref('odoo_job_costing_management.action_job_costing').read()[0]
            action['domain'] = [('id', 'in', job_cost.ids)]
        else:
            action = {
                'type': 'ir.actions.act_window',
                'res_model': 'job.costing',
                'view_mode': 'form',
                'res_id': job_cost.id,
                'target': 'current'
            }
        return action

    # @api.onchange('project_id')
    # def onchange_project_id(self):
    #     self.partner_id = self.project_id.partner_id

    def multi_action_confirm(self):
        ids = self.env.context.get('active_ids', [])
        job_quotaion_ids = self.browse(ids)
        for job_quotaion_id in job_quotaion_ids:
            job_quotaion_id.action_confirm()

    def multi_action_set_draft(self):
        ids = self.env.context.get('active_ids', [])
        job_quotaion_ids = self.browse(ids)
        for job_quotaion_id in job_quotaion_ids:
            job_quotaion_id.action_set_draft()

    @api.multi
    def action_confirm(self):
        for record in self:
            job_cost_line = []
            job_labour_line = []
            job_overhead_line = []
            for line in record.line_ids:
                data = {}
                if line.product_id:
                    data.update({
                        'date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'product_id' : line.product_id.id,
                        'description' : line.product_id.name,
                        'product_qty' : line.so_luong,
                        'uom_id' : line.product_id.uom_id.id,
                        'cost_price' : line.product_id.lst_price,
                    })
                    job_type_id = line.type
                    if job_type_id:
                        data.update({
                            'job_type_id' : job_type_id.id
                        })
                        if job_type_id.job_type == 'material':
                            data.update({
                                'job_type' : 'material',
                            })
                            job_cost_line.append((0,0,data))
                        elif job_type_id.job_type == 'labour':
                            data.update({
                                'job_type': 'labour',
                            })
                            job_labour_line.append((0,0,data))
                        else:
                            data.update({
                                'job_type': 'overhead',
                            })
                            job_overhead_line.append((0,0,data))
                    else:
                        data.update({
                            'job_type': 'material',
                        })
                        job_cost_line.append((0,0,data))

            job_costing = {
                # 'project_id' : record.project_id.id or False,
                # 'default_project_id' : record.project_id.id or False,
                # 'analytic_id': record.project_id.analytic_account_id.id or False,
                # 'partner_id' : record.partner_id.id,
                'default_start_date' : datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
                'default_name' : record.name or 'New',
                'default_job_cost_line_ids': job_cost_line,
                'default_job_labour_line_ids': job_labour_line,
                'default_job_overhead_line_ids': job_overhead_line,
            }
            # job_costing_id = self.env['job.costing'].create(job_costing)
            # record.job_costing_id = job_costing_id
            # record.state = 'done'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'job.costing',
            'view_mode': 'form',
            # 'res_id': job_costing_id.id,
            'res_id': False,
            'context': job_costing,
            'target': 'current'
        }

    @api.model
    def create(self, vals):
        res = super(job_quotaion, self).create(vals)
        res.job_quotaion_code = self.env['ir.sequence'].next_by_code('job.quotaion.code')
        sequence = 1
        for line in res.line_ids.sorted('id', reverse=False):
            line.sequence = sequence
            sequence += 1
        return res

    @api.multi
    def write(self, vals):
        res = super(job_quotaion, self).write(vals)
        for record in self:
            sequence = 1
            for line in record.line_ids.filtered(lambda l: l.sequence != 0).sorted('sequence', reverse=False):
                line.sequence = sequence
                sequence += 1
            for line in record.line_ids.filtered(lambda l: l.sequence == 0).sorted('sequence', reverse=False):
                line.sequence = sequence
                sequence += 1
        return res

    def export_job_quotaion_line(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('dinh muc so bo')

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 40)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 50)
        worksheet.set_column('G:K', 40)
        worksheet.set_column('L:L', 10)
        worksheet.set_column('M:M', 7)
        worksheet.set_column('N:N', 30)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['STT','Loại','Mã sản phẩm', 'Sản phẩm','Số sp tìm được', 'Mô tả', 'Từ khoá','Nhà sản xuất','Mã sản phẩm','Xuất xứ','Mã Đặt Hàng','Đ/V','S/L','Ghi chú']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for line in self.line_ids:
            row += 1
            worksheet.write(row, 0, line.sequence, body_bold_color)
            worksheet.write(row, 1, line.type.name or '', body_bold_color)
            worksheet.write(row, 2, line.product_id.default_code or '', body_bold_color)
            worksheet.write(row, 3, line.product_id.name or '', body_bold_color)
            worksheet.write(row, 4, line.number_product, body_bold_color)
            worksheet.write(row, 5, line.description, body_bold_color)
            worksheet.write(row, 6, line.key_word, body_bold_color)
            worksheet.write(row, 7, line.nha_san_xuat, body_bold_color)
            worksheet.write(row, 8, line.ma_san_pham, body_bold_color)
            worksheet.write(row, 9, line.xuat_su, body_bold_color)
            worksheet.write(row, 10, line.ma_dat_hang, body_bold_color)
            worksheet.write(row, 11, line.product_uom.name or '', body_bold_color)
            worksheet.write(row, 12, line.so_luong, body_bold_color)
            worksheet.write(row, 13, line.note, body_bold_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'dinh_muc_so_bo.xlsx',
            'datas_fname': 'dinh_muc_so_bo.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }

    def clear_all(self):
        if self.line_ids:
            self.line_ids.unlink()

    def import_data_excel(self):
        try:
            data = base64.b64decode(self.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)

            type = False
            line_ids = self.line_ids.browse([])
            for row_no in range(sheet.nrows):
                if row_no > 1:
                    row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                               sheet.row(row_no)))
                    if not row[0] and not row[1] and not row[2] and not row[3]:
                        break
                    if row[1] and not row[2] and not row[3] and not row[4] and not row[5] and not row[6] and not row[7] and not row[8]:
                        type = row[1]
                        type_id = self.env['job.type'].search([('name','=',type)],limit=1)
                        if not type_id:
                            type_id = self.env['job.type'].create({
                                'name' : type,
                                'job_type' : 'material',
                                'code' : type,
                            })
                        type = type_id
                    else:
                        product_uom_id = False
                        if row[2]:
                            self.env.cr.execute(
                                "SELECT id FROM product_uom WHERE lower(name) = '%s'" % (row[7].strip().lower()))
                            brand_names = self.env.cr.fetchall()
                            if brand_names:
                                product_uom_id = brand_names[0][0]
                        line_data = {
                            'type': type and type.id or False,
                            'description': row[1],
                            'key_word': row[2],
                            'nha_san_xuat': row[3],
                            'ma_san_pham': row[4],
                            'xuat_su': row[5],
                            'ma_dat_hang': row[6],
                            'product_uom': product_uom_id if product_uom_id else False,
                            'so_luong': row[8],
                            'note': row[9],
                        }
                        line = self.line_ids.new(line_data)
                        line.onchange_product_id()
                        line_ids += line
            self.line_ids += line_ids
        except:
            raise UserError('Lỗi format file nhập')


class job_quotaion_line(models.Model):
    _name = 'job.quotaion.line'

    sequence = fields.Integer(string="STT")
    product_id_deff = fields.Many2one('product.product', string="Sản phẩm khác")
    product_id = fields.Many2one('product.product',string="Sản phẩm")
    product_ids = fields.Char()
    number_product = fields.Integer(string="Số sp tìm được",compute='get_number_product')
    key_word = fields.Char(string="Từ khoá")
    type = fields.Many2one('job.type',string="Loại")
    description = fields.Text(string="Mô tả")
    nha_san_xuat = fields.Char(string="Nhà sản xuất")
    ma_san_pham = fields.Char(string="Mã sản phẩm")
    xuat_su = fields.Char(string="Xuất xứ")
    ma_dat_hang = fields.Char(string="Mã Đặt Hàng")
    product_uom = fields.Many2one('product.uom',string="Đ/V")
    so_luong = fields.Char(string="S/L")
    note = fields.Text(string="Ghi chú")
    job_quotaion_id = fields.Many2one('job.quotaion')
    product_child_ids = fields.Many2many('product.product', string='Phụ kiện')
    job_quotaion_sample = fields.Many2one('job.quotaion', string='Định mức mẫu')
    parent_id = fields.Many2one('job.quotaion.line', string="Parent")
    child_ids = fields.One2many('job.quotaion.line', 'parent_id', string="Childs")

    @api.onchange('product_ids')
    def get_number_product(self):
        for record in self:
            if record.product_ids:
                record.number_product = len(json.loads(record.product_ids))

    @api.multi
    def open_update_quotaion_product(self):
        action = self.env.ref('job_quotaion.update_quotaion_product_action').read()[0]
        action['context'] = {'job_quotaion_line': self.id}
        return action

    @api.multi
    def open_select_product_child(self):
        action = self.env.ref('job_quotaion.action_product_child_select_wizard').read()[0]
        if self.product_id and self.product_id.child_ids:
            product_ids = [child.product_id.product_variant_id.id for child in self.product_id.child_ids]
            action['context'] = {'domain': product_ids}
        return action

    @api.multi
    def add_new_line_after(self):
        line_id = self.create({
            'job_quotaion_id': self.job_quotaion_id.id,
            'sequence': self.sequence + 1
        })
        line_id.onchange_product_id()

        for line in self.job_quotaion_id.line_ids:
            if line.sequence > self.sequence and line != line_id:
                line.sequence += 1
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }

    @api.onchange('product_id_deff')
    def onchange_product_id_deff(self):
        for record in self:
            if record.product_id_deff:
                record.product_id = record.product_id_deff
                record.product_uom = record.product_id_deff.uom_id

    @api.onchange('product_id')
    def onchange_uom_product(self):
        for record in self:
            if record.product_id:
                record.product_uom = record.product_id.uom_id

    @api.onchange('key_word','nha_san_xuat','ma_san_pham','ma_dat_hang')
    def onchange_product_id(self):
        domain = []
        for record in self:
            if record.nha_san_xuat and record.nha_san_xuat != 'Nêu rõ':
                nha_san_xuat = []
                for nsx in record.nha_san_xuat.split(','):
                    if nsx.strip():
                        self.env.cr.execute(
                            "SELECT id FROM brand_name WHERE lower(name) = '%s'" % (nsx.strip().lower()))
                        brand_names = self.env.cr.fetchall()
                        for brand_name in brand_names:
                            nha_san_xuat.append(brand_name)
                domain.append(('product_tmpl_id.brand_name_select','in',nha_san_xuat))
            if record.ma_san_pham and record.ma_san_pham != 'Nêu rõ':
                domain.append(('default_code','ilike', record.ma_san_pham))
            if record.ma_dat_hang and record.ma_dat_hang != 'Nêu rõ':
                domain.append(('purchase_code','ilike',record.ma_dat_hang))
            if record.key_word and record.key_word != 'Nêu rõ':
                for key in record.key_word.split(' '):
                    product_key_word = []
                    if key:
                        self.env.cr.execute(
                            "SELECT id FROM product_template WHERE lower(name) LIKE '%s'" % ("%" + key.lower() + "%"))
                        products = self.env.cr.fetchall()
                        for product in products:
                            product_key_word.append(product)
                        domain.append(('product_tmpl_id','in',product_key_word))

            product_ids = self.env['product.product'].search(domain)
            if not record.product_id:
                if len(product_ids) == 1:
                    record.product_id = product_ids
                    if not record.product_uom:
                        record.product_uom = product_ids.uom_id
            else:
                if record.product_id not in product_ids:
                    if len(product_ids) == 1:
                        record.product_id = product_ids
                        if not record.product_uom:
                            record.product_uom = product_ids.uom_id
                    else:
                        record.product_id = False
            record.number_product = len(product_ids)
            record.product_ids = json.dumps(product_ids.ids)

    @api.model
    def create(self, vals):
        res = super(job_quotaion_line, self).create(vals)
        if vals.get('product_child_ids', False):
            if not vals.get('parent_id', False):
                sequence = 1
                for product in vals.get('product_child_ids', False)[0][2]:
                    product_ids = []
                    if product.child_ids:
                        product_ids = [child.product_id.product_variant_id.id for child in product.child_ids]

                    res.create({
                        'sequence': 0,
                        'type': res.type.id,
                        'parent_id': res.id,
                        'product_child_ids': [(6, 0, product.ids)],
                        'product_id': product.id,
                        'product_id_deff': product.id,
                        'description': product.name,
                        'product_uom': product.uom_id.id,
                        'list_price': product.lst_price,
                        'product_ids': json.dumps(product_ids),
                        'number_product': len(product_ids),
                    })
        return res

    @api.multi
    def write(self, vals):
        res = super(job_quotaion_line, self).write(vals)
        if vals.get('product_child_ids', False):
            for record in self:
                record.child_ids.unlink()
                sequence = 1
                for product in record.product_child_ids:
                    product_ids = []
                    if product.child_ids:
                        product_ids = [child.product_id.product_variant_id.id for child in product.child_ids]

                    record.create({
                        'sequence': 0,
                        'type': record.type.id,
                        'parent_id': record.id,
                        'product_child_ids': [(6,0, product.ids)],
                        'product_id': product.id,
                        'product_id_deff': product.id,
                        'description': product.name,
                        'product_uom': product.uom_id.id,
                        'list_price': product.lst_price,
                        'product_ids': json.dumps(product_ids),
                        'number_product': len(product_ids),
                    })
                    sequence += 1
        return res

class product_product(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if 'job_quo_product_ids' in self._context:
            if not self._context.get('job_quo_product_ids',False):
                args = []
            else:
                product_ids = self._context.get('job_quo_product_ids',False)
                product_ids = json.loads(product_ids)
                args.append(('id','in',product_ids))
        return super(product_product, self).name_search(name=name, args=args, operator=operator, limit=limit)



