# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook


class prinizi_modifier_sale(models.Model):
    _inherit = 'sale.order.line'

    check_box_prinizi_confirm = fields.Boolean(default=False, string="Confirm Print")
    print_qty = fields.Float(sting='Print Qty', digits=(16, 0))
    check_print = fields.Boolean(default=False)

    # @api.onchange('product_id')
    # def get_check_print(self):
    #     for rec in self:
    #         if self._context.get('quy_trinh_ban_hang',False) == 'noprint':
    #             rec.check_print = False
    #         else:
    #             rec.check_print = True

    @api.onchange('check_box_prinizi_confirm')
    def onchange_check_box_prinizi_confirm(self):
        if self.check_box_prinizi_confirm:
            if not self.print_qty:
                self.print_qty = self.product_uom_qty
        else:
            self.print_qty = 0

    @api.onchange('check_print')
    def onchange_check_print(self):
        if self.order_id.quy_trinh_ban_hang == 'print':
            self.check_print = True
        else:
            self.check_print = False

    @api.constrains('print_qty', 'product_uom_qty')
    def constrains_prinizi_sale_order_lines(self):
        for rec in self:
            if rec.print_qty > rec.product_uom_qty:
                raise ValidationError(_("Sản phẩm %s có số lượng in %s lớn hơn số lượng bán %s" % (
                    rec.product_id.display_name, rec.print_qty, rec.product_uom_qty)))
            elif rec.print_qty < 0:
                raise ValidationError(
                    _("Sản phẩm %s số lượng in %s không được bé hơn 0!" % (rec.product_id.display_name, rec.print_qty)))

    @api.onchange('print_qty', 'product_uom_qty')
    def check_print_qty(self):
        for rec in self:
            if rec.print_qty > rec.product_uom_qty:
                print_qty = rec.print_qty
                rec.print_qty = rec.product_uom_qty
                rec.check_box_prinizi_confirm = True
                # raise ValidationError(_("Sản phẩm %s có số lượng in %s lớn hơn số lượng bán %s" % (rec.product_id.display_name, rec.print_qty, rec.product_uom_qty)))
                return {
                    'warning': {
                        'title': "Error",
                        'message': "Sản phẩm %s có số lượng in %s lớn hơn số lượng bán %s, đã điều chỉnh số lượng in bằng số lượng bán %s !" % (
                            rec.product_id.display_name, print_qty, rec.product_uom_qty, rec.product_uom_qty),
                    }
                }
            if rec.print_qty < 0:
                raise ValidationError(
                    _("Sản phẩm %s số lượng in %s không được bé hơn 0!" % (rec.product_id.display_name, rec.print_qty)))
            elif rec.print_qty > 0:
                rec.check_box_prinizi_confirm = True
            else:
                rec.check_box_prinizi_confirm = False

    @api.model
    def create(self, val):
        res = super(prinizi_modifier_sale, self).create(val)
        if res.order_id:
            if res.order_id.quy_trinh_ban_hang == 'print':
                res.check_print = True
            else:
                res.check_print = False
            for i in range(0, int(res.print_qty)):
                product_id = res.product_id
                attribute_mau = product_id.attribute_value_ids.filtered(lambda p: p.attribute_id.name == 'Màu')
                if attribute_mau:
                    attribute_mau = attribute_mau[0]
                    product_print_id = self.env['product.print'].search(
                        [('product_id', '=', product_id.product_tmpl_id.id),
                         ('attribute_value_id', '=', attribute_mau.id)], limit=1)
                    if product_print_id:
                        self.env['thong.tin.its'].create({
                            'product_from_id': product_id.id,
                            'product_id': product_print_id.id,
                            'size': res.product_id.attribute_value_ids.filtered(
                                lambda p: p.attribute_id.name == 'Size').name or '',
                            'sale_id': res.order_id.id,
                        })
        return res

    @api.multi
    def write(self, val):
        if 'product_id' in val or 'print_qty' in val:
            for rec in self:
                product_id = rec.product_id
                attribute_mau = product_id.attribute_value_ids.filtered(lambda p: p.attribute_id.name == 'Màu')
                if attribute_mau:
                    attribute_mau = attribute_mau[0]
                    product_print_id = self.env['product.print'].search(
                        [('product_id', '=', product_id.product_tmpl_id.id),
                         ('attribute_value_id', '=', attribute_mau.id)], limit=1)
                    if product_print_id:
                        len_tt_its = self.env['thong.tin.its'].search(
                            [('product_from_id', '=', product_id.id), ('product_id', '=', product_print_id.id),
                             ('sale_id', '=', rec.order_id.id)])
                        if len_tt_its:
                            len_tt_its.unlink()

        res = super(prinizi_modifier_sale, self).write(val)
        if 'product_id' in val or 'print_qty' in val:
            for rec in self:
                if rec.order_id:
                    for i in range(0, int(rec.print_qty)):
                        product_id = rec.product_id
                        attribute_mau = product_id.attribute_value_ids.filtered(lambda p: p.attribute_id.name == 'Màu')
                        if attribute_mau:
                            attribute_mau = attribute_mau[0]
                            product_print_id = self.env['product.print'].search(
                                [('product_id', '=', product_id.product_tmpl_id.id),
                                 ('attribute_value_id', '=', attribute_mau.id)], limit=1)
                            if product_print_id:
                                self.env['thong.tin.its'].create({
                                    'product_from_id': product_id.id,
                                    'product_id': product_print_id.id,
                                    'size': rec.product_id.attribute_value_ids.filtered(
                                        lambda p: p.attribute_id.name == 'Size').name or '',
                                    'sale_id': rec.order_id.id,
                                })
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            product_id = rec.product_id
            attribute_mau = product_id.attribute_value_ids.filtered(lambda p: p.attribute_id.name == 'Màu')
            if attribute_mau:
                attribute_mau = attribute_mau[0]
                product_print_id = self.env['product.print'].search(
                    [('product_id', '=', product_id.product_tmpl_id.id),
                     ('attribute_value_id', '=', attribute_mau.id)], limit=1)
                if product_print_id:
                    len_tt_its = self.env['thong.tin.its'].search(
                        [('product_id', '=', product_print_id.id), ('sale_id', '=', rec.order_id.id)])
                    if len_tt_its:
                        len_tt_its.unlink()
        res = super(prinizi_modifier_sale, self).unlink()
        return res


class prinizi_modifier_sale_ihr(models.Model):
    _inherit = 'sale.order'

    check_box_prinizi = fields.Boolean(default=False, string="Confirm All Print")
    quy_trinh_ban_hang = fields.Selection([('print', 'Có In'), ('noprint', 'Không In')], required=False)
    thong_tin_its = fields.One2many('thong.tin.its', 'sale_id')
    thong_tin_them_its_ids = fields.One2many('thong.tin.them.its', 'sale_id')
    thong_tin_in_hinh_ids = fields.One2many('thong.tin.in.hinh', 'sale_id')
    config_thong_tin_its_ids = fields.One2many('config.thong.tin.its', 'sale_id')
    product_product_ids = fields.Char(compute='get_list_product_product', store=True)
    product_print_ids = fields.Char(compute='get_list_product', store=True)
    check_all_tt_its = fields.Boolean(string='Checkbox tất cả')
    phi_its = fields.Monetary(string='Phí in tên số', compute='_get_phi_its', store=True)
    phi_them_its = fields.Monetary(string='Phí in thêm tên số', compute='_get_phi_them_its', store=True)
    phi_in_hinh = fields.Monetary(string='Phí in hình', compute='_get_phi_in_hinh', store=True)
    tong_phi_in = fields.Monetary(string='Tổng phí in', compute='_get_tong_phi_in', store=True)
    data_ttits = fields.Binary(string='Data')
    data_ttits_name = fields.Char(string='Data Name')

    @api.multi
    def import_data_ttits(self):
        try:
            data = base64.b64decode(self.data_ttits)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            rownum = sheet.nrows - 1
            len_lines = len(self.thong_tin_its)
            row_len = rownum if rownum <= len_lines else len_lines
            i = 1
            for line in self.thong_tin_its:
                row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                           sheet.row(i)))
                row[3].strip().upper()
                try:
                    lung_tren = str(int(float(row[0])))
                except:
                    lung_tren = row[0].strip()
                try:
                    lung_giua = str(int(float(row[1])))
                except:
                    lung_giua = row[1].strip()
                try:
                    lung_duoi = str(int(float(row[2])))
                except:
                    lung_duoi = row[2].strip()
                data = {
                    'lung_tren': lung_tren,
                    'lung_giua': lung_giua,
                    'lung_duoi': lung_duoi,
                    'in_hinh': True if row[3].strip().upper() == 'YES' else False
                }
                line.write(data)
                i += 1
                if i > row_len:
                    break
        except:
            raise UserError('Lỗi format file nhập')


    @api.multi
    def action_draft(self):
        for rec in self:
            sale_data = rec.copy_data({})[0]
            if rec.sale_order_return:
                sale_data.update({
                    'reason_cancel': rec.reason_cancel.id,
                })
            sale_id = self.env['sale.order'].create(sale_data)
            rec.sale_set_draft_id = sale_id
            if rec.config_thong_tin_its_ids:
                sale_id.config_thong_tin_its_ids.unlink()
                for tti in rec.config_thong_tin_its_ids:
                    value_data = tti.copy_data({})[0]
                    value_data['sale_id'] = sale_id.id
                    self.env['config.thong.tin.its'].create(value_data)
            if rec.thong_tin_its:
                sale_id.thong_tin_its.unlink()
                for tti in rec.thong_tin_its:
                    value_data = tti.copy_data({})[0]
                    value_data['sale_id'] = sale_id.id
                    self.env['thong.tin.its'].create(value_data)
            if rec.thong_tin_them_its_ids:
                sale_id.thong_tin_them_its_ids.unlink()
                for tti in rec.thong_tin_them_its_ids:
                    value_data = tti.copy_data({})[0]
                    value_data['sale_id'] = sale_id.id
                    self.env['thong.tin.them.its'].create(value_data)
            if rec.thong_tin_in_hinh_ids:
                sale_id.thong_tin_in_hinh_ids.unlink()
                for tti in rec.thong_tin_in_hinh_ids:
                    value_data = tti.copy_data({})[0]
                    value_data['sale_id'] = sale_id.id
                    self.env['thong.tin.in.hinh'].create(value_data)
            sale_id.button_dummy()
            # sale_id.write({
            #     'phi_its': rec.phi_its,
            #     'phi_them_its': rec.phi_them_its,
            #     'phi_in_hinh': rec.phi_in_hinh,
            #     'tong_phi_in': rec.tong_phi_in,
            # })
            # if rec.phi_its:
            #         value = tti.copy()
            #         value.sale_id = sale_id
            if rec.sale_order_return:
                action = self.env.ref('sale_purchase_returns.sale_order_return_action').read()[0]
                action['views'] = [[self.env.ref('sale.view_order_form').id, 'form']]
                action['res_id'] = sale_id.id
                return action
            else:
                action = self.env.ref('sale.action_orders').read()[0]
                action['views'] = [[self.env.ref('sale.view_order_form').id, 'form']]
                action['res_id'] = sale_id.id
                return action

    @api.multi
    def button_dummy(self):
        self.onchange_order_line()
        res = super(prinizi_modifier_sale_ihr, self).button_dummy()
        for order in self:
            amount_total = order.amount_total
            tong_phi_in = order.tong_phi_in
            order.update({
                'amount_total': amount_total + tong_phi_in
            })
        return res

    @api.depends('order_line')
    def get_list_product_product(self):
        for rec in self:
            rec.product_product_ids = json.dumps(rec.order_line.mapped('product_id').ids)

    @api.depends('phi_its', 'phi_them_its', 'phi_in_hinh')
    def _get_tong_phi_in(self):
        for rec in self:
            rec.tong_phi_in = rec.phi_its + rec.phi_them_its + rec.phi_in_hinh

    @api.depends('thong_tin_its', 'config_thong_tin_its_ids')
    def _get_phi_its(self):
        for rec in self:
            phi_its = 0
            for line in rec.thong_tin_its:
                count_lung_tren_duoi = 0
                count_lung_giua = 0
                if line.lung_tren:
                    count_lung_tren_duoi += 1
                if line.lung_duoi:
                    count_lung_tren_duoi += 1
                if line.lung_giua:
                    count_lung_giua += 1

                config_thong_tin_its_ids = self.env['config.thong.tin.its'].search(
                    [('product_id', '=', line.product_id.id), ('sale_id', '=', line.sale_id.id)], limit=1)
                lung_ao_chat_lieu_its = config_thong_tin_its_ids.lung_ao_chat_lieu_its

                if lung_ao_chat_lieu_its:
                    phi_its += count_lung_tren_duoi * lung_ao_chat_lieu_its.phi_in
                    phi_its += count_lung_giua * lung_ao_chat_lieu_its.phi_in * lung_ao_chat_lieu_its.he_so_dien_tich

            rec.phi_its = phi_its

    @api.depends('thong_tin_them_its_ids', 'config_thong_tin_its_ids', 'thong_tin_its')
    def _get_phi_them_its(self):
        for rec in self:
            phi_them_its = 0
            for line in rec.thong_tin_them_its_ids:
                thong_tin_its = self.env['thong.tin.its'].search(
                    [('product_id', '=', line.product_id.id), ('sale_id', '=', line.sale_id.id)])
                count_thong_tin_its = len(thong_tin_its)

                vi_tri_in = line.vi_tri_in
                config_thong_tin_its_ids = self.env['config.thong.tin.its'].search(
                    [('product_id', '=', line.product_id.id), ('sale_id', '=', line.sale_id.id)], limit=1)
                phi_in = 0
                if vi_tri_in.code in ['lung_ao_tren', 'lung_ao_giua', 'lung_ao_duoi']:
                    phi_in = config_thong_tin_its_ids.lung_ao_chat_lieu_its.phi_in
                elif vi_tri_in.code in ['mat_truoc_ao_nguc_phai', 'mat_truoc_ao_nguc_trai', 'mat_truoc_ao_bung']:
                    phi_in = config_thong_tin_its_ids.mat_truoc_ao_chat_lieu_its.phi_in
                elif vi_tri_in.code in ['ong_quan_trai', 'ong_quan_phai']:
                    phi_in = config_thong_tin_its_ids.ong_quan_chat_lieu_its.phi_in
                elif vi_tri_in.code in ['tay_ao_trai', 'tay_ao_phai']:
                    phi_in = config_thong_tin_its_ids.tay_ao_chat_lieu_its.phi_in

                phi_them_its += count_thong_tin_its * phi_in * line.dien_tich_in.he_so_dien_tich
            rec.phi_them_its = phi_them_its

    @api.depends('thong_tin_in_hinh_ids', 'thong_tin_its')
    def _get_phi_in_hinh(self):
        for rec in self:
            phi_in_hinh = 0
            for line in rec.thong_tin_in_hinh_ids:
                thong_tin_its = self.env['thong.tin.its'].search(
                    [('product_id', '=', line.product_id.id), ('sale_id', '=', line.sale_id.id),
                     ('in_hinh', '=', True)])
                count_thong_tin_its = len(thong_tin_its)
                phi_in_hinh += count_thong_tin_its * line.chat_lieu_in_hinh.phi_in * line.dien_tich_in.he_so_dien_tich
            rec.phi_in_hinh = phi_in_hinh

    @api.onchange('check_all_tt_its')
    def onchange_check_all_tt_its(self):
        for rec in self:
            if rec.check_all_tt_its:
                for line in rec.thong_tin_its:
                    line.in_hinh = True
            else:
                for line in rec.thong_tin_its:
                    line.in_hinh = False

    @api.depends('thong_tin_its')
    def get_list_product(self):
        for rec in self:
            rec.product_print_ids = json.dumps(rec.thong_tin_its.mapped('product_id').ids)

    @api.onchange('check_box_prinizi')
    def onchange_check_box_prinizi(self):
        for rec in self:
            if rec.check_box_prinizi:
                if rec.order_line:
                    for line in rec.order_line:
                        line.check_box_prinizi_confirm = True
                        if not line.print_qty:
                            line.print_qty = line.product_uom_qty
                            # else:
                            #     if rec.order_line:
                            #         for line in rec.order_line:
                            #             line.check_box_prinizi_confirm = False

    @api.onchange('quy_trinh_ban_hang')
    def onchange_quy_trinh_ban_hang(self):
        for rec in self:
            if rec.quy_trinh_ban_hang == 'noprint':
                if rec.order_line:
                    for line in rec.order_line:
                        line.check_print = False
                        line.check_box_prinizi_confirm = False
                        line.print_qty = 0
                    rec.check_box_prinizi = False
            else:
                for line in rec.order_line:
                    line.check_print = True

    @api.model
    def prinizi_so_export_print(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        sale_ids = self.env['sale.order'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sale Export Print')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1})
        body_bold_color_blue = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
             'bg_color': '#6CACDD', 'border': 1})
        body_bold_color_green = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
             'bg_color': '#B7D79F', 'border': 1})
        body_bold_color_yellow = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
             'bg_color': '#FFFB00', 'border': 1})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'border': 1})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'border': 1})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('E:AY', 12)
        worksheet.set_column('A:D', 20)

        row = 0
        col = -1

        summary_header = ['Mã SO', 'Thời gian', 'Mã khách hàng', 'Tên khách hàng']
        for header_cell in range(0, len(summary_header)):
            if summary_header[header_cell]:
                col += 1
                worksheet.write(row, col, unicode(summary_header[header_cell], "utf-8"), body_bold_color_blue)
        summary_header = []

        chat_lieu_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_ten_so')
        chat_lieu_its_list = self.env['prinizi.product.attribute.value'].search(
            [('attribute', '=', chat_lieu_in_ten_so.id)])
        if chat_lieu_its_list:
            for chat_lieu in chat_lieu_its_list:
                chat_lieu = str(chat_lieu.name)
                summary_header += ['Số chi tiết in tên (%s)' % (chat_lieu), 'Tổng phí in tên (%s)' % (chat_lieu)]
            for header_cell in range(0, len(summary_header)):
                if summary_header[header_cell]:
                    col += 1
                    worksheet.write(row, col, unicode(summary_header[header_cell], "utf-8"), body_bold_color)
            summary_header = []
            for chat_lieu in chat_lieu_its_list:
                chat_lieu = str(chat_lieu.name)
                summary_header += ['Số chi tiết in số (%s)' % (chat_lieu), 'Tổng phí in số (%s)' % (chat_lieu)]
            for header_cell in range(0, len(summary_header)):
                if summary_header[header_cell]:
                    col += 1
                    worksheet.write(row, col, unicode(summary_header[header_cell], "utf-8"), body_bold_color_green)
            summary_header = []
            for chat_lieu in chat_lieu_its_list:
                chat_lieu = str(chat_lieu.name)
                summary_header += ['Số chi tiết in thêm tên số (%s)' % (chat_lieu),
                                   'Tổng phí in thêm tên số (%s)' % (chat_lieu)]
            for header_cell in range(0, len(summary_header)):
                if summary_header[header_cell]:
                    col += 1
                    worksheet.write(row, col, unicode(summary_header[header_cell], "utf-8"), body_bold_color)
            summary_header = []

        chat_lieu_in_hinh = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_hinh')
        chat_lieu_in_hinh_list = self.env['prinizi.product.attribute.value'].search(
            [('attribute', '=', chat_lieu_in_hinh.id)])
        if chat_lieu_in_hinh_list:
            for chat_lieu_ih in chat_lieu_in_hinh_list:
                chat_lieu_ih = str(chat_lieu_ih.name)
                summary_header += ['Số chi tiết in hình (%s)' % (chat_lieu_ih),
                                   'Tổng phí in hình (%s)' % (chat_lieu_ih)]
            for header_cell in range(0, len(summary_header)):
                if summary_header[header_cell]:
                    col += 1
                    worksheet.write(row, col, unicode(summary_header[header_cell], "utf-8"), body_bold_color_green)
            summary_header = []
        if chat_lieu_its_list:
            for chat_lieu in chat_lieu_its_list:
                chat_lieu = str(chat_lieu.name)
                summary_header += ['Số chi tiết in quần (%s)' % (chat_lieu)]
            for header_cell in range(0, len(summary_header)):
                if summary_header[header_cell]:
                    col += 1
                    worksheet.write(row, col, unicode(summary_header[header_cell], "utf-8"), body_bold_color)
            summary_header = []

        summary_header += ['Tổng phí in']
        for header_cell in range(0, len(summary_header)):
            if summary_header[header_cell]:
                col += 1
                worksheet.write(row, col, unicode(summary_header[header_cell], "utf-8"), body_bold_color_yellow)
        summary_header = []

        summary_header += ['Trạng thái đơn hàng', 'Trạng thái hoạt động']
        for header_cell in range(0, len(summary_header)):
            if summary_header[header_cell]:
                col += 1
                worksheet.write(row, col, unicode(summary_header[header_cell], "utf-8"), body_bold_color_blue)
        summary_header = []

        for sale_id in sale_ids:
            tong_phi_in = 0
            row += 1
            date_order = ''
            if sale_id.confirmation_date:
                date_order = self._get_datetime_utc(sale_id.confirmation_date)
            worksheet.write(row, 0, sale_id.name, text_style)
            worksheet.write(row, 1, date_order, text_style)
            worksheet.write(row, 2, sale_id.partner_id.ref, text_style)
            worksheet.write(row, 3, sale_id.partner_id.name, text_style)
            count_col = 3
            for chat_lieu in chat_lieu_its_list:
                count_lung_tren_duoi = 0
                for config_line in sale_id.config_thong_tin_its_ids:
                    if config_line.lung_ao_chat_lieu_its == chat_lieu:
                        thong_tin_its = self.env['thong.tin.its'].search(
                            [('product_id', '=', config_line.product_id.id), ('sale_id', '=', sale_id.id)])
                        for line_tt_its in thong_tin_its:
                            if line_tt_its.lung_tren:
                                count_lung_tren_duoi += 1
                            if line_tt_its.lung_duoi:
                                count_lung_tren_duoi += 1
                count_col += 1
                worksheet.write(row, count_col, count_lung_tren_duoi, text_style)
                count_col += 1
                worksheet.write(row, count_col, count_lung_tren_duoi * chat_lieu.phi_in, body_bold_color_number)
                tong_phi_in += count_lung_tren_duoi * chat_lieu.phi_in

            for chat_lieu in chat_lieu_its_list:
                count_lung_giua = 0
                for config_line in sale_id.config_thong_tin_its_ids:
                    if config_line.lung_ao_chat_lieu_its == chat_lieu:
                        thong_tin_its = self.env['thong.tin.its'].search(
                            [('product_id', '=', config_line.product_id.id), ('sale_id', '=', sale_id.id)])
                        for line_tt_its in thong_tin_its:
                            if line_tt_its.lung_giua:
                                count_lung_giua += 1
                count_col += 1
                worksheet.write(row, count_col, count_lung_giua, text_style)
                count_col += 1
                worksheet.write(row, count_col, count_lung_giua * chat_lieu.phi_in * chat_lieu.he_so_dien_tich,
                                body_bold_color_number)
                tong_phi_in += count_lung_giua * chat_lieu.phi_in * chat_lieu.he_so_dien_tich

            for chat_lieu in chat_lieu_its_list:
                count_detail_ttt_its = 0
                for line_ttt_its in sale_id.thong_tin_them_its_ids:
                    thong_tin_its = self.env['thong.tin.its'].search(
                        [('product_id', '=', line_ttt_its.product_id.id), ('sale_id', '=', sale_id.id)])
                    count_thong_tin_its = len(thong_tin_its)

                    vi_tri_in = line_ttt_its.vi_tri_in
                    config_thong_tin_its_ids = self.env['config.thong.tin.its'].search(
                        [('product_id', '=', line_ttt_its.product_id.id), ('sale_id', '=', sale_id.id)], limit=1)

                    if vi_tri_in.code in ['lung_ao_tren', 'lung_ao_giua', 'lung_ao_duoi']:
                        if config_thong_tin_its_ids.lung_ao_chat_lieu_its == chat_lieu:
                            count_detail_ttt_its += count_thong_tin_its * line_ttt_its.dien_tich_in.he_so_dien_tich
                    elif vi_tri_in.code in ['mat_truoc_ao_nguc_phai', 'mat_truoc_ao_nguc_trai',
                                            'mat_truoc_ao_bung']:
                        if config_thong_tin_its_ids.lung_ao_chat_lieu_its == chat_lieu:
                            count_detail_ttt_its += count_thong_tin_its * line_ttt_its.dien_tich_in.he_so_dien_tich
                    elif vi_tri_in.code in ['ong_quan_trai', 'ong_quan_phai']:
                        if config_thong_tin_its_ids.lung_ao_chat_lieu_its == chat_lieu:
                            count_detail_ttt_its += count_thong_tin_its * line_ttt_its.dien_tich_in.he_so_dien_tich
                    elif vi_tri_in.code in ['tay_ao_trai', 'tay_ao_phai']:
                        if config_thong_tin_its_ids.lung_ao_chat_lieu_its == chat_lieu:
                            count_detail_ttt_its += count_thong_tin_its * line_ttt_its.dien_tich_in.he_so_dien_tich
                count_col += 1
                worksheet.write(row, count_col, count_detail_ttt_its, text_style)
                count_col += 1
                worksheet.write(row, count_col, count_detail_ttt_its * chat_lieu.phi_in, body_bold_color_number)
                tong_phi_in += count_detail_ttt_its * chat_lieu.phi_in
            for chat_lieu_ih in chat_lieu_in_hinh_list:
                count_detail_in_hinh = 0
                for line_tt_in_hinh in sale_id.thong_tin_in_hinh_ids:
                    if line_tt_in_hinh.chat_lieu_in_hinh == chat_lieu_ih:
                        thong_tin_its = self.env['thong.tin.its'].search(
                            [('product_id', '=', line_tt_in_hinh.product_id.id), ('sale_id', '=', sale_id.id),
                             ('in_hinh', '=', True)])
                        count_thong_tin_its = len(thong_tin_its)
                        count_detail_in_hinh += count_thong_tin_its * line_tt_in_hinh.dien_tich_in.he_so_dien_tich
                count_col += 1
                worksheet.write(row, count_col, count_detail_in_hinh, text_style)
                count_col += 1
                worksheet.write(row, count_col, count_detail_in_hinh * chat_lieu_ih.phi_in, body_bold_color_number)
                tong_phi_in += count_detail_in_hinh * chat_lieu_ih.phi_in

            for chat_lieu in chat_lieu_its_list:
                count_lung_giua = 0
                for config_line in sale_id.config_thong_tin_its_ids:
                    if config_line.lung_ao_chat_lieu_its == chat_lieu:
                        thong_tin_its = self.env['thong.tin.its'].search(
                            [('product_id', '=', config_line.product_id.id), ('sale_id', '=', sale_id.id)])
                        for line_tt_its in thong_tin_its:
                            if line_tt_its.lung_giua:
                                count_lung_giua += 1
                count_col += 1
                worksheet.write(row, count_col, count_lung_giua, text_style)

            count_col += 1
            worksheet.write(row, count_col, tong_phi_in, body_bold_color_number)

            trang_thai_don_hang = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                                           'selection'])[sale_id.state] if sale_id.state else ''
            count_col += 1
            worksheet.write(row, count_col, trang_thai_don_hang, text_style)

            trang_thai_hoat_dong = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_dh'])['trang_thai_dh'][
                                            'selection'])[sale_id.trang_thai_dh] if sale_id.trang_thai_dh else ''
            count_col += 1
            worksheet.write(row, count_col, trang_thai_hoat_dong, text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


class product_product_ihr(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if 'product_ids' in self._context:
            product_ids = self._context.get('product_ids', False)
            if product_ids:
                product_ids = json.loads(product_ids)
                args += [('id', 'in', product_ids)]
            else:
                args += [('id', 'in', [])]
        res = super(product_product_ihr, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return res
