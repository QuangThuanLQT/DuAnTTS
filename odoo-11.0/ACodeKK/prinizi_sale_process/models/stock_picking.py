# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, date
import StringIO
import xlsxwriter
import pytz
from odoo.exceptions import UserError, ValidationError

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    produce_name_state = fields.Selection([('draft', 'Draft'),
                                           ('waiting_produce', 'Waiting'),
                                           ('ready_produce', 'Ready'),
                                           ('produce', 'Producing'),
                                           ('done', 'Done'),
                                           ('cancel', 'Cancel')], default='waiting_produce', string="Produce Name state")

    produce_image_state = fields.Selection([('draft', 'Draft'),
                                            ('waiting_produce', 'Waiting'),
                                            ('ready_produce', 'Ready'),
                                            ('produce', 'Producing'),
                                            ('done', 'Done'),
                                            ('cancel', 'Cancel')], default='waiting_produce', string="Produce Image state")

    kcs1_state = fields.Selection([('draft', 'Draft'),
                                   ('waiting', 'Waiting'),
                                   ('ready', 'Ready'),
                                   ('done', 'Done'),
                                   ('cancel', 'Cancel')], default='waiting', string="KCS1 state")

    print_state = fields.Selection([('draft', 'Draft'),
                                    ('waiting_print', 'Waiting'),
                                    ('ready_print', 'Ready'),
                                    ('print', 'Printing'),
                                    ('done', 'Done'),
                                    ('cancel', 'Cancel')], default='waiting_print', string="Produce Image state")

    kcs2_state = fields.Selection([('draft', 'Draft'),
                                   ('waiting', 'Waiting'),
                                   ('ready', 'Ready'),
                                   ('done', 'Done'),
                                   ('cancel', 'Cancel')], default='waiting', string="KCS2 state")

    internal_sale_type = fields.Selection([('draft', 'Draft'),
                                          ('ready', 'Ready'),
                                          ('done', 'Done'),
                                          ('cancel', 'Cancel')], default='draft', string="Internal Sale state")

    check_produce_name = fields.Boolean(compute='_get_check_produce_name')
    check_produce_image = fields.Boolean(compute='_get_check_produce_image')
    check_kcs1 = fields.Boolean(compute='_get_check_kcs1')
    check_kcs2 = fields.Boolean(compute='_get_check_kcs2')
    check_print = fields.Boolean(compute='_get_check_print')

    location_id = fields.Many2one('stock.location', required=False)
    location_dest_id = fields.Many2one('stock.location', required=False)
    picking_type = fields.Selection([('pick', 'Pick'),
                                     ('pack', 'Pack'),
                                     ('delivery', 'Delivery'),
                                     ('reciept', 'Receipt'),
                                     ('internal', 'Internal'),
                                     ('produce_name', 'Produce Name'),
                                     ('produce_image', 'Produce Image'),
                                     ('print', 'Print'),
                                     ('kcs1', 'KCS1'),
                                     ('kcs2', 'KCS2'),
                                     ('internal_sale', 'Internal Sale'),
                                     ], string='Type', related='picking_type_id.picking_type', store=True)
    state_pick_default = fields.Char()
    produce_name_state_default = fields.Char()
    produce_image_state_default = fields.Char()
    kcs1_state_default = fields.Char()
    print_state_default = fields.Char()
    kcs2_state_default = fields.Char()
    state_pack_default = fields.Char()
    state_delivery_default = fields.Char()
    date_internal_sale = fields.Date(string='Ngày đặt hàng')
    sum_qty_internal_sale = fields.Integer(string='Tổng số lượng', compute='get_total_internal_sale')
    sum_total_internal_sale = fields.Float(string='Tổng thành tiền', compute='get_total_internal_sale')
    picking_note = fields.Char(compute=False, string='Diễn giải', store=True)

    @api.model
    def internal_sale_export_overview(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        picking_ids = self.env['stock.picking'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Internal Sale Export Overview')
        worksheet.set_column('A:F', 20)
        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'border': 1})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0'})

        summary_header = ['Thời gian tạo', 'Nhân viên mua', 'Nhân viên tạo', 'Ghi chú', 'Tổng thành tiền','Trạng thái hoạt động']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for picking_id in picking_ids:
            row += 1
            date_base_order = ''
            # if picking_id.date_base_order:
            #     date_base_order = self._get_datetime_utc(picking_id.date_base_order)
            trang_thai = dict(self.fields_get(allfields=['internal_sale_type'])['internal_sale_type']['selection'])
            worksheet.write(row, 0, picking_id.date_base_order or '', text_style)
            worksheet.write(row, 1, picking_id.user_internal_sale.name or '', text_style)
            worksheet.write(row, 2, picking_id.create_uid.name or '', text_style)
            worksheet.write(row, 3, picking_id.note or '', text_style)
            worksheet.write(row, 4, picking_id.sum_total_internal_sale, body_bold_color_number)
            worksheet.write(row, 5, trang_thai.get(picking_id.internal_sale_type) if picking_id.internal_sale_type else '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def internal_sale_export_detail(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        picking_ids = self.env['stock.picking'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Internal Sale Export Detail')
        worksheet.set_column('A:N', 20)
        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'border': 1})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0'})

        summary_header = ['Mã phiếu bán nội bộ','Ngày đặt hàng', 'Nhân viên mua', 'Nhân viên bán hàng', 'Ghi chú','Mã biến thể nội bộ','Tên sản phẩm', 'Màu',
                          'Size','Số lượng', 'Price Unit','Subtotal', 'Tổng thành tiền','Trạng thái hoạt động']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for picking_id in picking_ids:
            product_ids = picking_id.move_lines.mapped('product_id')
            trang_thai = dict(self.fields_get(allfields=['internal_sale_type'])['internal_sale_type']['selection'])
            # date_base_order = ''
            # if picking_id.date_base_order:
            #     date_base_order = self._get_datetime_utc(picking_id.date_base_order)
            # if len(product_ids) <= 1:
            #     worksheet.write(row + 1, 0, picking_id.name, text_style)
            #     worksheet.write(row + 1, 1, picking_id.date_base_order, text_style)
            #     worksheet.write(row + 1, 2, picking_id.user_internal_sale.name or '', text_style)
            #     worksheet.write(row + 1, 3, picking_id.create_uid.name or '', text_style)
            #     worksheet.write(row + 1, 4, picking_id.note or '', text_style)
            #     worksheet.write(row + 1, 12, picking_id.sum_total_internal_sale, body_bold_color_number)
            #     worksheet.write(row + 1, 13,
            #                     trang_thai.get(picking_id.internal_sale_type) if picking_id.internal_sale_type else '',
            #                     text_style)
            # else:
            #     worksheet.merge_range(row + 1, 0, row + len(product_ids), 0, picking_id.name, text_style)
            #     worksheet.merge_range(row + 1, 1, row + len(product_ids), 1, picking_id.date_base_order, text_style)
            #     worksheet.merge_range(row + 1, 2, row + len(product_ids), 2, picking_id.user_internal_sale.name or '', text_style)
            #     worksheet.merge_range(row + 1, 3, row + len(product_ids), 3, picking_id.create_uid.name or '', text_style)
            #     worksheet.merge_range(row + 1, 4, row + len(product_ids), 4, picking_id.note or '', text_style)
            #     worksheet.merge_range(row + 1, 12, row + len(product_ids), 12, picking_id.sum_total_internal_sale, text_style)
            #     worksheet.merge_range(row + 1, 13, row + len(product_ids), 13, trang_thai.get(picking_id.internal_sale_type) if picking_id.internal_sale_type else '', text_style)

            for product_id in product_ids:
                move_lines = self.env['stock.move'].search([('picking_id', '=', picking_id.id), ('product_id', '=', product_id.id)])
                row += 1
                mau = ''
                if product_id.attribute_value_ids:
                    mau = product_id.attribute_value_ids.filtered(lambda attr: attr.attribute_id.name in ['Màu','màu'])
                    if mau:
                        mau = mau[0].name

                size = ''

                if product_id.attribute_value_ids:
                    size = product_id.attribute_value_ids.filtered(
                        lambda attr: attr.attribute_id.name in ['Size', 'size'])
                    if size:
                        size = size[0].name
                worksheet.write(row, 0, picking_id.name, text_style)
                worksheet.write(row, 1, picking_id.date_base_order, text_style)
                worksheet.write(row, 2, picking_id.user_internal_sale.name or '', text_style)
                worksheet.write(row, 3, picking_id.create_uid.name or '', text_style)
                worksheet.write(row, 4, picking_id.note or '', text_style)
                worksheet.write(row, 5, product_id.default_code, text_style)
                worksheet.write(row, 6, product_id.name, text_style)
                worksheet.write(row, 7, mau, text_style)
                worksheet.write(row, 8, size, text_style)
                worksheet.write(row, 9, sum(move_lines.mapped('product_uom_qty')), text_style)
                worksheet.write(row, 10, sum(move_lines.mapped('internal_sale_price')), body_bold_color_number)
                worksheet.write(row, 11, sum(move_lines.mapped('internal_sale_sub_total')), body_bold_color_number)
                worksheet.write(row, 12, picking_id.sum_total_internal_sale, body_bold_color_number)
                worksheet.write(row, 13,
                                trang_thai.get(picking_id.internal_sale_type) if picking_id.internal_sale_type else '',
                                text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def onchange_line_value_price(self):
        for rec in self:
            line_data = {}
            promotion_data = {}
            for line in rec.move_lines:
                if line.product_id:
                    line_data.update({
                        str(line.product_id.product_tmpl_id): line_data.get(str(line.product_id.product_tmpl_id),
                                                                            0) + line.product_uom_qty
                    })
            if line_data:
                template_list = rec.move_lines.mapped('product_id.product_tmpl_id')
                for template in template_list:
                    qty_tem = line_data.get(str(template), False)
                    now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    pricelist = self.env['product.pricelist.line'].search([
                        ('line_id', '=', template.id),
                        ('start_date', '<=', now),
                        ('end_date', '>=', now),
                        ('quantity_min', '<=', qty_tem)
                    ], order='quantity_min DESC', limit=1)
                    if pricelist:
                        promotion_data.update({
                            str(template): pricelist.giam_gia
                        })
            for line in rec.move_lines:
                pricelist_tem = promotion_data.get(str(line.product_id.product_tmpl_id), False)
                print pricelist_tem
                if pricelist_tem:
                    line.internal_sale_price = line.product_id.lst_price - pricelist_tem
                else:
                    line.internal_sale_price = line.product_id.lst_price

    @api.multi
    def get_total_internal_sale(self):
        for rec in self:
            rec.sum_qty_internal_sale = sum(rec.move_lines.mapped('product_uom_qty'))
            rec.sum_total_internal_sale = sum(rec.move_lines.mapped('internal_sale_sub_total'))

    @api.multi
    def _get_date_order(self):
        for record in self:
            print 'dsadjgashjdhjashjdhjsagdjgsajd'
            if record.sale_id:
                record.date_base_order = record.sale_id.confirmation_date
            elif record.purchase_id:
                record.date_base_order = record.purchase_id.confirmation_date
            elif record.date_internal_sale:
                print '11111111gsajd'
                record.date_base_order = record.date_internal_sale

    @api.multi
    def get_picking_state_show(self):
        for rec in self:
            if rec.check_is_pick:
                state_pick = dict(self.fields_get(['state_pick'])['state_pick']['selection'])
                rec.picking_state_show = state_pick[rec.state_pick]
            elif rec.check_is_pack:
                state_pack = dict(self.fields_get(['state_pack'])['state_pack']['selection'])
                if rec.state_pack == 'waiting_pick':
                    rec.picking_state_show = state_pack['waiting_pack']
                else:
                    rec.picking_state_show = state_pack[rec.state_pack]
            elif rec.check_is_delivery:
                state_delivery = dict(self.fields_get(['state_delivery'])['state_delivery']['selection'])
                rec.picking_state_show = state_delivery[rec.state_delivery]
            elif rec.is_internal_transfer:
                internal_transfer_state = dict(
                    self.fields_get(['internal_transfer_state'])['internal_transfer_state']['selection'])
                rec.picking_state_show = internal_transfer_state[rec.internal_transfer_state]
            elif rec.picking_type_code == 'incoming':
                receipt_state = dict(self.fields_get(['receipt_state'])['receipt_state']['selection'])
                rec.picking_state_show = receipt_state[rec.receipt_state]
            elif rec.check_produce_name:
                produce_name_state = dict(self.fields_get(['produce_name_state'])['produce_name_state']['selection'])
                rec.picking_state_show = produce_name_state[rec.produce_name_state]
            elif rec.check_produce_image:
                produce_image_state = dict(self.fields_get(['produce_image_state'])['produce_image_state']['selection'])
                rec.picking_state_show = produce_image_state[rec.produce_image_state]
            elif rec.check_kcs1:
                kcs1_state = dict(self.fields_get(['kcs1_state'])['kcs1_state']['selection'])
                rec.picking_state_show = kcs1_state[rec.kcs1_state]
            elif rec.check_kcs2:
                kcs2_state = dict(self.fields_get(['kcs2_state'])['kcs2_state']['selection'])
                rec.picking_state_show = kcs2_state[rec.kcs2_state]
            elif rec.check_print:
                print_state = dict(self.fields_get(['print_state'])['print_state']['selection'])
                rec.picking_state_show = print_state[rec.print_state]
            elif rec.picking_type == 'internal_sale':
                internal_sale_type = dict(self.fields_get(['internal_sale_type'])['internal_sale_type']['selection'])
                rec.picking_state_show = internal_sale_type[rec.internal_sale_type]
            else:
                state = dict(self.fields_get(['state'])['state']['selection'])
                rec.picking_state_show = state[rec.state]

    # TODO button produce_name
    @api.multi
    def pname_action_confirm(self):
        for rec in self:
            if rec.produce_name_state == 'draft':
                rec.produce_name_state = 'waiting_produce'
                rec.state = 'confirmed'
            elif rec.produce_name_state == 'waiting_produce':
                rec.produce_name_state = 'ready_produce'
                rec.state = 'assigned'

    @api.multi
    def pname_action_assign(self):
        for rec in self:
            # rec.action_confirm()
            rec.produce_name_state = 'produce'


    @api.multi
    def pname_action_do_new_transfer(self):
        for rec in self:
            rec.produce_name_state = 'done'
            rec.state = 'done'
                # return rec.do_new_transfer()
            if not rec.is_picking_return:
                kcs1_id = rec.sale_id.picking_ids.filtered(lambda r: r.check_kcs1 == True)
                pick_id = rec.sale_id.picking_ids.filtered(lambda r: r.check_is_pick == True)
                product_image = rec.sale_id.picking_ids.filtered(lambda r: r.check_produce_image == True)
                if pick_id.state == 'done' and product_image.state == 'done':
                    if kcs1_id:
                        kcs1_id.action_assign()
                        kcs1_id.write({
                            'kcs1_state': 'ready',
                        })


    # TODO button produce_image

    @api.multi
    def pimg_action_confirm(self):
        for rec in self:
            if rec.produce_image_state == 'draft':
                rec.produce_image_state = 'waiting_produce'
                rec.state = 'confirmed'
            elif rec.produce_image_state == 'waiting_produce':
                rec.produce_image_state = 'ready_produce'
                rec.state = 'assigned'

    @api.multi
    def pimg_action_assign(self):
        for rec in self:
            # rec.action_confirm()
            rec.produce_image_state = 'produce'

    @api.multi
    def pimg_action_do_new_transfer(self):
        for rec in self:
            rec.produce_image_state = 'done'
            rec.state = 'done'
                # return rec.do_new_transfer()
            if not rec.is_picking_return:
                kcs1_id = rec.sale_id.picking_ids.filtered(lambda r: r.check_kcs1 == True)
                pick_id = rec.sale_id.picking_ids.filtered(lambda r: r.check_is_pick == True)
                check_produce_name = rec.sale_id.picking_ids.filtered(lambda r: r.check_produce_name == True)
                if pick_id.state == 'done' and check_produce_name.state == 'done':
                    if kcs1_id:
                        kcs1_id.action_assign()
                        kcs1_id.write({
                            'kcs1_state': 'ready',
                        })

    # TODO button kcs1

    @api.multi
    def kcs1_action_confirm(self):
        for rec in self:
            if rec.kcs1_state == 'draft':
                rec.kcs1_state = 'waiting'
            elif rec.kcs1_state == 'waiting':
                rec.kcs1_state = 'ready'

    @api.multi
    def kcs1_action_assign(self):
        for rec in self:
            rec.action_confirm()
            rec.action_assign()
            rec.kcs1_state = 'ready'

    @api.multi
    def kcs1_action_do_new_transfer(self):
        for rec in self:
            if rec.state == 'assigned':
                rec.kcs1_state = 'done'
                return rec.do_new_transfer()
            else:
                rec.action_assign()
                if rec.state == 'assigned':
                    rec.kcs1_state = 'done'
                    return rec.do_new_transfer()


    # TODO button print

    @api.multi
    def print_action_confirm(self):
        for rec in self:
            if rec.print_state == 'draft':
                rec.print_state = 'waiting_print'
            elif rec.print_state == 'waiting_print':
                rec.print_state = 'ready_print'

    @api.multi
    def print_action_assign(self):
        for rec in self:
            rec.action_confirm()
            rec.print_state = 'print'

    @api.multi
    def print_action_do_new_transfer(self):
        for rec in self:
            if rec.state == 'assigned':
                rec.print_state = 'done'
                return rec.do_new_transfer()
            else:
                rec.action_assign()
                if rec.state == 'assigned':
                    rec.print_state = 'done'
                    return rec.do_new_transfer()

    # TODO button kcs2

    @api.multi
    def kcs2_action_confirm(self):
        for rec in self:
            if rec.kcs2_state == 'draft':
                rec.kcs2_state = 'waiting'
            elif rec.kcs2_state == 'waiting':
                rec.kcs2_state = 'ready'

    @api.multi
    def kcs2_action_assign(self):
        for rec in self:
            rec.action_confirm()
            rec.kcs2_state = 'ready'

    @api.multi
    def kcs2_action_do_new_transfer(self):
        for rec in self:
            if rec.state == 'assigned':
                rec.kcs2_state = 'done'
                return rec.do_new_transfer()
            else:
                rec.action_assign()
                if rec.state == 'assigned':
                    rec.kcs2_state = 'done'
                    return rec.do_new_transfer()

    # TODO button internal sale

    @api.multi
    def internal_sale_action_confirm(self):
        for rec in self:
            if rec.internal_sale_type == 'draft':
                rec.action_confirm()
                rec.internal_sale_type = 'ready'
            rec.write({
                'time_accept': fields.Datetime.now(),
            })

    @api.multi
    def internal_sale_action_do_new_transfer(self):
        for rec in self:
            for line in rec.move_lines:
                if line.product_uom_qty > (line.product_id.sp_co_the_ban + line.product_uom_qty):
                    raise ValidationError(
                        _('Bạn định bán %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                            line.product_uom_qty, line.product_id.display_name,
                            line.product_id.sp_co_the_ban + line.product_uom_qty)))
            if rec.state == 'assigned':
                rec.internal_sale_type = 'done'
                rec.date_internal_sale = datetime.now().date()
                return rec.do_new_transfer()
            else:
                rec.action_assign()
                if rec.state == 'assigned':
                    rec.date_internal_sale = datetime.now().date()
                    rec.internal_sale_type = 'done'
                    return rec.do_new_transfer()
                else:
                    for line in rec.move_lines:
                        if line.state in ['waiting','confirmed']:
                            raise UserError('Sản phẩm %s không có đủ trong kho.' % (line.product_id.name))


    @api.depends('picking_type_id')
    def _get_check_produce_name(self):
        for record in self:
            if record.picking_type_id.picking_type == 'produce_name':
                record.check_produce_name = True

    @api.depends('picking_type_id')
    def _get_check_produce_image(self):
        for record in self:
            if record.picking_type_id.picking_type == 'produce_image':
                record.check_produce_image = True

    @api.depends('picking_type_id')
    def _get_check_kcs1(self):
        for record in self:
            if record.picking_type_id.picking_type == 'kcs1':
                record.check_kcs1 = True

    @api.depends('picking_type_id')
    def _get_check_kcs2(self):
        for record in self:
            if record.picking_type_id.picking_type == 'kcs2':
                record.check_kcs2 = True

    @api.depends('picking_type_id')
    def _get_check_print(self):
        for record in self:
            if record.picking_type_id.picking_type == 'print':
                record.check_print = True

    @api.multi
    @api.onchange('picking_type_id')
    def _get_check_is_pick(self):
        for rec in self:
            rec.check_is_pick = False
            rec.check_is_pack = False
            rec.check_is_delivery = False
            if rec.picking_type_id and rec.picking_type_id.picking_type == 'pick':
                rec.check_is_pick = True
            elif rec.picking_type_id and rec.picking_type_id.picking_type == 'pack':
                rec.check_is_pack = True
            elif rec.picking_type_id and rec.picking_type_id.picking_type == 'delivery':
                rec.check_is_delivery = True

    @api.onchange('picking_type_id')
    def check_is_internal_transfer(self):
        for record in self:
            if record.picking_type_id.picking_type == 'internal':
                record.is_internal_transfer = True
            else:
                record.is_internal_transfer = False

    @api.onchange('picking_type_id')
    def check_is_orther_picking(self):
        for record in self:
            if record.picking_type_id.picking_type == False:
                record.is_orther_picking = True
            else:
                record.is_orther_picking = False

    @api.multi
    def write(self, vals):
        if 'produce_name_state' in vals:
            for rec in self:
                old_state = rec.produce_name_state
                new_state = vals.get('produce_name_state')
                state = dict(self.fields_get(['produce_name_state'])['produce_name_state']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        if 'produce_image_state' in vals:
            for rec in self:
                old_state = rec.produce_image_state
                new_state = vals.get('produce_image_state')
                state = dict(self.fields_get(['produce_image_state'])['produce_image_state']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        if 'kcs1_state' in vals:
            for rec in self:
                old_state = rec.kcs1_state
                new_state = vals.get('kcs1_state')
                state = dict(self.fields_get(['kcs1_state'])['kcs1_state']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        if 'print_state' in vals:
            for rec in self:
                old_state = rec.print_state
                new_state = vals.get('print_state')
                state = dict(self.fields_get(['print_state'])['print_state']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        if 'kcs2_state' in vals:
            for rec in self:
                old_state = rec.kcs2_state
                new_state = vals.get('kcs2_state')
                state = dict(self.fields_get(['kcs2_state'])['kcs2_state']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        res =  super(stock_picking, self).write(vals)
        # if not self._context.get('non_update', False):
        #     for rec in self:
        #         rec.with_context(non_update=True).onchange_line_value_price()
        if 'state_pick' in vals and vals['state_pick'] == 'ready_pick':
            for record in self:
                if record.sale_id:
                    product_name = record.sale_id.picking_ids.filtered(lambda r: r.check_produce_name == True)
                    if product_name:
                        product_name.produce_name_state = 'ready_produce'

        return res

    @api.model
    def create(self, vals):
        res = super(stock_picking, self).create(vals)
        # res.with_context(non_update=True).onchange_line_value_price()
        return res

    @api.multi
    def print_delivery_export_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        domain.append(('picking_type_id.code', '=', 'outgoing'))
        domain.append(('state', '!=', 'cancel'))
        picking_ids = self.env['stock.picking'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Delivery time log')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:U', 20)

        summary_header = ['Mã đơn hàng bán (SO)', 'Mã đơn trả hàng NCC (Return)', 'Thời gian tạo Sale Quotation',
                          'Thời gian tạo phiếu Pick có Pick status = Waiting',
                          'Thời gian tạo phiếu Pick có Pick status =  Ready',
                          'Thời gian tạo phiếu Pick có Pick status = Picking',
                          'Thời gian tạo phiếu Pick có Pick status = done',
                          'Thời gian tạo phiếu PRC_NAME có PRC_NAME status = Producing',
                          'Thời gian tạo phiếu PRC_NAME có PRC_NAME status = Done',
                          'Thời gian tạo phiếu PRC_IMG có PRC_IMG status = Producing',
                          'Thời gian tạo phiếu PRC_IMG có PRC_IMG status = Done',
                          'Thời gian tạo phiếu KCS1 có KCS1 status = Ready',
                          'Thời gian tạo phiếu Print có Print status = Ready',
                          'Thời gian tạo phiếu Print có Print status = Printing',
                          'Thời gian tạo phiếu KCS2 có KCS2 status = Ready',
                          'Thời gian tạo phiếu Pack có Pack status = Waiting',
                          'Thời gian tạo phiếu Pack có Pack status = Packing',
                          'Thời gian tạo phiếu Delivery có Delivery status = Waiting',
                          'Thời gian tạo phiếu Delivery có Delivery status = Delivering',
                          'Thời gian tạo phiếu Delivery có Delivery status = Done',
                          'Trạng thái đơn hàng']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for picking_id in picking_ids:
            if (
                picking_id.sale_id or picking_id.purchase_id) and not picking_id.check_is_pick and not picking_id.check_is_pack:
                row += 1
                row_0 = row_1 = row_2 = row_3 = row_4 = row_5 = row_6 = row_7 = row_8 = row_9 = row_10 = row_11 = \
                    row_12 = row_13 = row_14 = row_15 = row_16 = row_17 = row_18 = row_19 = row_20 = ''
                if picking_id.sale_id:
                    row_0 = picking_id.sale_id.name
                    row_2 = self._get_datetime_utc(picking_id.sale_id.date_order)
                    picking_pick = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_is_pick)
                    if picking_pick:
                        picking_pick = picking_pick[0]
                        for line in picking_pick.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                row_3 = self._get_datetime_utc(picking_pick.sale_id.confirmation_date)
                                if state == 'Waiting':
                                    row_3 = self._get_datetime_utc(line.time_log)
                                elif state == 'Ready':
                                    row_4 = self._get_datetime_utc(line.time_log)
                                elif state == 'Picking':
                                    row_5 = self._get_datetime_utc(line.time_log)
                                elif state == 'Done':
                                    row_6 = self._get_datetime_utc(line.time_log)

                    picking_produce_name = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_produce_name)
                    if picking_produce_name:
                        picking_produce_name = picking_produce_name[0]
                        for line in picking_produce_name.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Producing':
                                    row_7 = self._get_datetime_utc(line.time_log)
                                elif state == 'Done':
                                    row_8 = self._get_datetime_utc(line.time_log)

                    picking_image_state = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_produce_image)
                    if picking_image_state:
                        picking_image_state = picking_image_state[0]
                        for line in picking_image_state.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Producing':
                                    row_9 = self._get_datetime_utc(line.time_log)
                                elif state == 'Done':
                                    row_10 = self._get_datetime_utc(line.time_log)

                    picking_kcs1_state = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_kcs1)
                    if picking_kcs1_state:
                        picking_kcs1_state = picking_kcs1_state[0]
                        for line in picking_kcs1_state.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Ready':
                                    row_11 = self._get_datetime_utc(line.time_log)

                    picking_print_state = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_print)
                    if picking_print_state:
                        picking_print_state = picking_print_state[0]
                        for line in picking_print_state.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Ready':
                                    row_12 = self._get_datetime_utc(line.time_log)
                                elif state == 'Printing':
                                    row_13 = self._get_datetime_utc(line.time_log)

                    picking_kcs2_state = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_kcs2)
                    if picking_kcs2_state:
                        picking_kcs2_state = picking_kcs2_state[0]
                        for line in picking_kcs2_state.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Ready':
                                    row_14 = self._get_datetime_utc(line.time_log)

                    picking_pack = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_is_pack)
                    if picking_pack:
                        picking_pack = picking_pack[0]
                        for line in picking_pack.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Waiting':
                                    row_15 = self._get_datetime_utc(line.time_log)
                                elif state == 'Packing':
                                    row_16 = self._get_datetime_utc(line.time_log)

                    for line in picking_id.stock_picking_log_ids:
                        if line.status_changed:
                            state = line.status_changed.split('->')[1].strip()
                            if state == 'Waiting':
                                row_17 = self._get_datetime_utc(line.time_log)
                            elif state == 'Delivering':
                                row_18 = self._get_datetime_utc(line.time_log)
                            elif state == 'Done':
                                row_19 = self._get_datetime_utc(line.time_log)

                    state = dict(self.env['sale.order'].fields_get(['trang_thai_dh'])['trang_thai_dh']['selection'])
                    if picking_id.sale_id.trang_thai_dh:
                        row_20 = state[picking_id.sale_id.trang_thai_dh]
                    else:
                        row_20 = ''
                elif picking_id.purchase_id:
                    row_1 = picking_id.purchase_id.name
                    row_2 = self._get_datetime_utc(picking_id.purchase_id.date_order)
                    picking_pick = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_is_pick)
                    if picking_pick:
                        picking_pick = picking_pick[0]
                        for line in picking_pick.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                row_3 = self._get_datetime_utc(picking_pick.purchase_id.confirmation_date)
                                if state == 'Waiting':
                                    row_3 = self._get_datetime_utc(line.time_log)
                                elif state == 'Ready':
                                    row_4 = self._get_datetime_utc(line.time_log)
                                elif state == 'Picking':
                                    row_5 = self._get_datetime_utc(line.time_log)
                                elif state == 'Done':
                                    row_6 = self._get_datetime_utc(line.time_log)

                    picking_produce_name = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_produce_name)
                    if picking_produce_name:
                        picking_produce_name = picking_produce_name[0]
                        for line in picking_produce_name.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Producing':
                                    row_7 = self._get_datetime_utc(line.time_log)
                                elif state == 'Done':
                                    row_8 = self._get_datetime_utc(line.time_log)

                    picking_image_state = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_produce_image)
                    if picking_image_state:
                        picking_image_state = picking_image_state[0]
                        for line in picking_image_state.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Producing':
                                    row_9 = self._get_datetime_utc(line.time_log)
                                elif state == 'Done':
                                    row_10 = self._get_datetime_utc(line.time_log)

                    picking_kcs1_state = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_kcs1)
                    if picking_kcs1_state:
                        picking_kcs1_state = picking_kcs1_state[0]
                        for line in picking_kcs1_state.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Ready':
                                    row_11 = self._get_datetime_utc(line.time_log)

                    picking_print_state = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_print)
                    if picking_print_state:
                        picking_print_state = picking_print_state[0]
                        for line in picking_print_state.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Ready':
                                    row_12 = self._get_datetime_utc(line.time_log)
                                elif state == 'Printing':
                                    row_13 = self._get_datetime_utc(line.time_log)

                    picking_kcs2_state = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_kcs2)
                    if picking_kcs2_state:
                        picking_kcs2_state = picking_kcs1_state[0]
                        for line in picking_kcs2_state.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Ready':
                                    row_14 = self._get_datetime_utc(line.time_log)

                    picking_pack = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_is_pack)
                    if picking_pack:
                        picking_pack = picking_pack[0]
                        for line in picking_pack.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Waiting':
                                    row_15 = self._get_datetime_utc(line.time_log)
                                elif state == 'Packing':
                                    row_16 = self._get_datetime_utc(line.time_log)

                    for line in picking_id.stock_picking_log_ids:
                        if line.status_changed:
                            state = line.status_changed.split('->')[1].strip()
                            if state == 'Waiting':
                                row_17 = self._get_datetime_utc(line.time_log)
                            elif state == 'Delivering':
                                row_18 = self._get_datetime_utc(line.time_log)
                            elif state == 'Done':
                                row_19 = self._get_datetime_utc(line.time_log)

                    if picking_id.purchase_id.operation_state:
                        row_20 = dict(
                            picking_id.purchase_id.fields_get(['operation_state'])['operation_state']['selection'])[
                            picking_id.purchase_id.operation_state]

                # state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                #                  'selection'])
                worksheet.write(row, 0, row_0, text_style)
                worksheet.write(row, 1, row_1, text_style)
                worksheet.write(row, 2, row_2, text_style)
                worksheet.write(row, 3, row_3, text_style)
                worksheet.write(row, 4, row_4, text_style)
                worksheet.write(row, 5, row_5, text_style)
                worksheet.write(row, 6, row_6, text_style)
                worksheet.write(row, 7, row_7, text_style)
                worksheet.write(row, 8, row_8, text_style)
                worksheet.write(row, 9, row_9, text_style)
                worksheet.write(row, 10, row_10, text_style)
                worksheet.write(row, 11, row_11, text_style)
                worksheet.write(row, 12, row_12, text_style)
                worksheet.write(row, 13, row_13, text_style)
                worksheet.write(row, 14, row_14, text_style)
                worksheet.write(row, 15, row_15, text_style)
                worksheet.write(row, 16, row_16, text_style)
                worksheet.write(row, 17, row_17, text_style)
                worksheet.write(row, 18, row_18, text_style)
                worksheet.write(row, 19, row_19, text_style)
                worksheet.write(row, 20, row_20, text_style)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
