# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import base64
from xlrd import open_workbook
import StringIO
import xlsxwriter
from datetime import datetime

class stock_internal_type(models.Model):
    _name = 'stock.internal.type'

    name        = fields.Char("Tên")

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    sale_select_id          = fields.Many2one('sale.order', 'Đơn hàng')
    is_picking_type_out     = fields.Boolean(compute='get_is_picking_type_out')
    type_id                 = fields.Many2one('stock.internal.type',string="Loại vật tư")
    mrp_production          = fields.Many2one('mrp.production','Lệnh sản xuất',domain=[('state','not in',['done','cancel'])])
    don_hang                = fields.Char(compute='get_don_hang',string="Đơn hàng")
    import_stock_data       = fields.Binary(string="Tải file của bạn lên")
    min_date                = fields.Datetime(states={'done': [('readonly', False)], 'cancel': [('readonly', False)]})
    purchase_id_base_origin = fields.Many2one('purchase.order',string='Đơn hàng Mua',compute='_get_purchase_id_base_origin')
    stock_out_ids           = fields.Many2many('stock.picking','stock_out_picking_rel','incoming_id','stock_out_id',string='Đơn xuất')
    stock_out_count         = fields.Integer(compute='get_stock_out_count')
    mrp_picking_id = fields.Many2one('stock.picking', string='Dịch chuyển sản xuất')
    partner_id              = fields.Many2one('res.partner',copy=False)
    job_quotaion_id         = fields.Many2one('job.quotaion', 'Định mức')


    @api.onchange('job_quotaion_id')
    def load_product_to_move_line_from_job_quotaion_id(self):
        if self.job_quotaion_id:
            for line in self.job_quotaion_id.line_ids:
                manufacture_id = self.env.ref('mrp.route_warehouse0_manufacture')
                if line.product_id and line.product_id and manufacture_id in line.product_id.route_ids:
                    continue

                obj = self.move_lines.with_context({
                    'address_in_id': self.partner_id.id,
                    'default_picking_type_id': self.picking_type_id.id,
                    'default_location_id': self.location_id.id,
                    'default_location_dest_id': self.location_dest_id.id,
                    'min_date': self.min_date
                })
                data_line = obj.default_get(obj._fields)
                data_line.update({
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'product_uom_qty': line.so_luong,
                    'name' : line.product_id.name,
                    'stt' : line.sequence,
                })
                self.move_lines += self.move_lines.new(data_line)

    @api.multi
    def confirm_and_validate_picking(self):
        for rec in self:
            rec.action_confirm()
            rec.action_assign()
            if rec.state == 'assigned':
                return rec.do_new_transfer()
        return True

    @api.depends('picking_type_id')
    def get_is_picking_type_out(self):
        project_transfer       = self.env.ref('cptuanhuy_stock.project_transfer')
        manufacturing_transfer = self.env.ref('cptuanhuy_stock.manufacturing_transfer')
        for record in self:
            if record.picking_type_id.id not in [project_transfer.id, manufacturing_transfer.id]:
                record.is_picking_type_out = True
            else:
                record.is_picking_type_out = False

    @api.multi
    def write(self,val):
        res = super(stock_picking, self).write(val)
        if 'min_date' in val:
            min_date = val.get('min_date',False)
            if min_date:
                for rec in self:
                    for line in rec.move_lines:
                        line.date = min_date

        return res


    @api.multi
    def get_stock_out_count(self):
        for record in self:
            record.stock_out_count = len(record.stock_out_ids)

    @api.multi
    def action_view_stock_out(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', self.stock_out_ids.ids)]
        action['context'] = {
            'search_default_wh_stock'   : True,
        }
        return action

    @api.multi
    def load_product_to_move_line(self):
        if self.mrp_production:
            for line in self.mrp_production.bom_id.bom_line_ids:
                manufacture_id = self.env.ref('mrp.route_warehouse0_manufacture')
                if line.product_id and line.product_id and manufacture_id in line.product_id.route_ids:
                    continue

                obj = self.move_lines.with_context({
                    'address_in_id': self.partner_id.id,
                    'default_picking_type_id': self.picking_type_id.id,
                    'default_location_id': self.location_id.id,
                    'default_location_dest_id': self.location_dest_id.id,
                    'min_date': self.min_date
                })
                data_line = obj.default_get(obj._fields)
                data_line.update({
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'product_uom_qty': line.product_qty,
                    'name' : line.product_id.name,
                    'stt' : line.sequence,
                })
                self.move_lines += self.move_lines.new(data_line)

    def _get_purchase_id_base_origin(self):
        for rec in self:
            if rec.purchase_id:
                rec.purchase_id_base_origin = rec.purchase_id
            elif rec.origin:
                purchase_id = self.env['purchase.order'].search([('name','=',rec.origin)],limit=1)
                rec.purchase_id_base_origin = purchase_id

    @api.multi
    def create_line_procurement_order(self):
        for rec in self:
            for line in rec.move_lines:
                if not line.procurement_id:
                    obj = self.env['procurement.order']
                    pro_order = obj.sudo().default_get(obj._fields)
                    pro_order.update({
                        'product_id' : line.product_id.id,
                        'product_qty' : line.product_uom_qty,
                        'product_uom' : line.product_uom.id,
                        'location_id' : line.location_id.id,
                        'origin' : line.picking_id.name,
                        'name' : line.picking_id.note or "Create from ->" + line.picking_id.name,
                        # 'partner_dest_id' : line.picking_id.partner_shipping_id.id,
                    })
                    procurement_id = obj.create(pro_order)
                    line.procurement_id = procurement_id
                else:
                    if line.procurement_id.state in ('confirmed','exception'):
                        line.procurement_id.run()

    @api.multi
    def create_purchase_request(self):
        data_line = []
        purchase_request_line_obj = self.env['purchase.request.line']

        pickings = self
        if self.env.context.get('active_model') == 'stock.picking':
            active_ids = self.env.context.get('active_ids')
            pickings = self.browse(active_ids)

        already_request_lines = purchase_request_line_obj.search([('sale_id','in',self.mapped('sale_select_id').ids)]).mapped('stock_move_id')

        for record in pickings:
            for line in record.move_lines.filtered(lambda line: line.id not in already_request_lines.ids):
                line_default_data = purchase_request_line_obj.default_get(purchase_request_line_obj._fields)
                line_default_data.update({
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom.id,
                    'product_qty': line.product_uom_qty,
                    'name': line.product_id.name,
                    'date_required': record.min_date,
                    'sale_id'   : record.sale_select_id.id or False,
                    'analytic_account_id' : record.sale_select_id.contract_id.id or False,
                    'stock_move_id' : line.id or False,
                    # 'min_date'          : self.min_date
                })
                data_line.append((0, 0, line_default_data))

        context = {
            # 'default_picking_type_id': self.env.ref("cptuanhuy_stock.manufacturing_transfer").id or False,
            # 'default_mrp_production': self.id,
            # 'default_sale_select_id': self.so_id.id or False,
            # 'default_shipper': self.user_id.id or False,
            # 'default_receiver': self.user_id.id or False,
            # 'default_partner_id': self.so_id and self.so_id.partner_id.id or False
        }
        if data_line:
            context.update({'default_line_ids': data_line})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Request',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref("purchase_request.view_purchase_request_form").id or False,
            'res_model': 'purchase.request',
            'context': context,
        }

    @api.multi
    def action_open_mo(self):
        mo_ids = []
        procurement_ids = self.mapped('move_lines').mapped('procurement_id')
        for procurement_id in procurement_ids:
            mo_id = self.env['mrp.production'].search([('procurement_ids', '=', procurement_id.id)])
            if mo_id:
                mo_ids.append(mo_id.id)
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('id', 'in', mo_ids)]
        action['context'] = {'default_origin': self.name or ''}
        return action

    @api.model
    def create_stock_picking_type(self):
        type_manufacturing_in = self.env['stock.picking.type'].search([
            ('name', '=', 'Nhập kho thành phẩm'),
            ('code', '=', 'internal')
        ], limit=1)
        if not type_manufacturing_in:
            data = self.env.ref('stock.picking_type_internal').copy_data({})[0]
            default_location_src_id = data.get('default_location_src_id',False)
            default_location_dest_id = data.get('default_location_dest_id',False)
            data.update({
                'name' : 'Nhập kho thành phẩm',
                'default_location_src_id' : default_location_dest_id,
                'default_location_dest_id': default_location_src_id,
            })
            type_manufacturing_in = self.env['stock.picking.type'].create(data)

            self.env['ir.model.data'].create({
                'name': 'manufacturing_in',
                'module': 'cptuanhuy_stock',
                'model': 'stock.picking.type',
                'res_id': type_manufacturing_in.id,
                'noupdate': True,
            })

        type_project_transfer = self.env['stock.picking.type'].search([
            ('name', '=', 'Dịch chuyển công trình'),
            ('code', '=', 'internal')
        ], limit=1)
        if not type_project_transfer:
            data = self.env.ref('stock.picking_type_internal').copy_data({})[0]
            default_location_src_id = data.get('default_location_src_id', False)
            data.update({
                'name': 'Dịch chuyển công trình',
                'default_location_src_id': default_location_src_id,
                'default_location_dest_id': self.env.ref('cptuanhuy_stock.location_kct_stock').id or False,
            })
            type_project_transfer = self.env['stock.picking.type'].create(data)

            self.env['ir.model.data'].create({
                'name': 'project_transfer',
                'module': 'cptuanhuy_stock',
                'model': 'stock.picking.type',
                'res_id': type_project_transfer.id,
                'noupdate': True,
            })

        try:
            type_manufacturing_transfer = self.env['stock.picking.type'].search([
                ('name', '=', 'Dịch chuyển sản xuất'),
                ('code', '=', 'internal')
            ])
            if not type_manufacturing_transfer:
                data = self.env.ref('stock.picking_type_internal').copy_data({})[0]
                default_location_src_id = data.get('default_location_src_id', False)
                data.update({
                    'name': 'Dịch chuyển sản xuất',
                    'default_location_src_id': default_location_src_id,
                    'default_location_dest_id': self.env.ref('cptuanhuy_mrp.location_ksx_stock').id or False,
                })
                type_manufacturing_transfer = self.env['stock.picking.type'].create(data)

                self.env['ir.model.data'].create({
                    'name': 'manufacturing_transfer',
                    'module': 'cptuanhuy_stock',
                    'model': 'stock.picking.type',
                    'res_id': type_manufacturing_transfer.id,
                    'noupdate': True,
                })
        except:
            pass

    def export_stock_data_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('%s' % (self.name))

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 50)

        header_bold_color = workbook.add_format({'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format({'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        # body_bold_color_number = workbook.add_format({'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        # body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['Mã nội bộ', 'SL','Sản phẩm']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for line in self.move_lines:
            row += 1
            worksheet.write(row, 0, line.product_id.default_code)
            worksheet.write(row, 1, line.product_uom_qty)
            worksheet.write(row, 2, line.product_id.name)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': '%s.xlsx'%(self.name),
            'datas_fname': '%s.xlsx'%(self.name),
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }

    @api.multi
    def import_stock_data_excel(self):
        for record in self:
            if record.import_stock_data:
                data = base64.b64decode(record.import_stock_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)
                move_lines = record.move_lines.browse([])

                row_error = []
                for row_no in range(sheet.nrows):
                    if row_no > 0:
                        row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),sheet.row(row_no)))
                        product = self.env['product.product'].search(['|', ('default_code', '=', row[0].strip()),('barcode', '=', row[0].strip())], limit=1)
                        if not product or int(float(row[1])) < 0:
                            row_error.append({
                                'default_code': row[0],
                                'qty'         : row[1],
                            })
                if row_error:
                    return {
                        'name': 'Import Warning',
                        'type': 'ir.actions.act_window',
                        'res_model': 'import.warning',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'data': row_error,
                        }
                    }
                else:

                    for row_no in range(sheet.nrows):
                        if row_no > 0:
                            row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                            if len(row) >= 2:
                                product = self.env['product.product'].search(['|', ('default_code', '=', row[0].strip()),('barcode', '=', row[0].strip())], limit=1)
                                if product and product.id:
                                    line_data = {
                                        'product_id': product.id,
                                        'product_uom': product.uom_id.id,
                                        'name': product.partner_ref,
                                        'product_uom_qty': int(float(row[1])),
                                        'location_id': record.location_id.id or False,
                                        'location_dest_id': record.location_dest_id.id or False,
                                        'stt'       : row_no,
                                    }

                                    line = record.move_lines.new(line_data)
                                    move_lines += line
                    record.move_lines = move_lines

    @api.multi
    def get_don_hang(self):
        for rec in self:
            if rec.sale_select_id:
                rec.don_hang = rec.sale_select_id.name
            elif rec.sale_id:
                rec.don_hang = rec.sale_id.name
            elif rec.purchase_id:
                rec.don_hang = rec.purchase_id.name
            else:
                rec.don_hang = ""

    @api.onchange('sale_select_id')
    def onchange_sale_select_id(self):
        if self.sale_select_id:
            if 'active_id' in self._context and 'active_model' in self._context and self._context['active_model'] == 'stock.picking':
                True
            # if not self.origin:
            else:
                self.origin = self.sale_select_id.name
            if self.picking_type_id and self.picking_type_id.code == 'outgoing':
                if not self.partner_id:
                    self.partner_id = self.sale_select_id.partner_id

            sale_id = self.sale_select_id
            mo_ids = []
            procurement_group_ids = sale_id.procurement_group_id
            picking_ids = self.env['stock.picking'].search([('sale_select_id', '=', sale_id.id)])
            procurement_picking_ids = picking_ids.mapped('move_lines').mapped('procurement_id').ids
            procurement_ids = self.env['procurement.order'].search(['|', ('group_id', 'in', procurement_group_ids.ids), ('id', 'in', procurement_picking_ids)])
            for procurement_id in procurement_ids:
                mo_id = self.env['mrp.production'].search([('procurement_ids', '=', procurement_id.id)])
                if mo_id:
                    mo_ids.append(mo_id.id)
            production_ids = self.env['mrp.production'].search([
                '|',
                ('origin', 'like', '%' + sale_id.name + '%'),
                ('so_id', '=', sale_id.id)
            ])
            for record in production_ids:
                if record.id not in mo_ids:
                    mo_ids.append(record.id)

            # if self.picking_type_id and self.picking_type_id.code in ['outgoing', 'internal']:
            if not self.partner_id:
                self.partner_id = self.sale_select_id.partner_id
            return {
                'domain': {
                    'mrp_production': [
                        ('id', 'in', mo_ids)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'mrp_production': []
                }
            }

    @api.onchange('mrp_production')
    def onchange_mrp_production(self):
        if self.mrp_production and not self.sale_select_id:
            self.sale_select_id = self.mrp_production.so_id


    # @api.multi
    # @api.depends('procurement_group_id')
    # def _compute_picking_ids(self):
    #     for order in self:
    #         order.picking_ids = self.env['stock.picking'].search([('group_id', '=', order.procurement_group_id.id)]) if order.procurement_group_id else []
    #         order.delivery_count = len(order.picking_ids)

    @api.multi
    def print_excel(self):
        self.ensure_one()

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        name = ''
        # if not self.check_return_picking and self.origin:
        #     if 'SO' in self.origin:
        #         name = 'PHIẾU XUẤT KHO BÁN HÀNG'
        #     elif 'PO' in self.origin:
        #         name = 'PHIẾU NHẬP KHO MUA HÀNG'
        if not self.check_return_picking:
            if 'WH/OUT' in self.name or 'XK' in self.name:
                name = 'PHIẾU XUẤT KHO'
            elif ('WH/IN' in self.name and 'WH/INT' not in self.name) or 'NK' in self.name:
                name = 'PHIẾU NHẬP KHO'
            elif 'WH/INT' in self.name:
                name = 'DỊCH CHUYỂN NỘI BỘ'
        if self.check_color_picking == 'red':
            name = 'PHIẾU NHẬP KHO TRẢ HÀNG'
        elif self.check_color_picking == 'blue':
            name = 'PHIẾU XUẤT KHO TRẢ HÀNG'

        string_sheet = 'Xuất phiếu kho'
        worksheet = workbook.add_worksheet(string_sheet)
        bold = workbook.add_format({'bold': True})

        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter'
        })
        header_bold_border_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        body_bold_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter'
        })
        body_bold_center_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter'
        })
        body_bold_border_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        # back_color =
        # back_color_date =

        worksheet.merge_range('A1:D1', self.company_id.name, body_bold_color)
        worksheet.merge_range('A2:D2', self.company_id.street, body_bold_color)

        string_header = name
        worksheet.merge_range('C3:E3', unicode(string_header, "utf-8"), merge_format)
        date = datetime.strptime(self.min_date, DEFAULT_SERVER_DATETIME_FORMAT)
        string = "Ngày %s tháng %s năm %s" % (date.day, date.month, date.year)
        worksheet.merge_range('C4:E4', unicode(string, "utf-8"), header_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)

        worksheet.merge_range('A5:E5', 'Người giao hàng:', body_bold_color)
        worksheet.merge_range('A6:E6', 'Tên khách hàng: %s' % (self.partner_id.name or self.sale_select_id.partner_id.name or  ''), body_bold_color)
        worksheet.merge_range('A7:E7', 'Địa chỉ: %s' % (self.partner_id.street or self.sale_select_id.partner_id.street or ''), body_bold_color)
        worksheet.merge_range('A8:E8', 'Diễn giải: %s' % (self.note or self.partner_id and ("Bán hàng %s" % (self.partner_id.name or '')) or ''),
                              body_bold_color)
        # worksheet.merge_range('A9:F9', 'Điện thoại: %s' % (self.partner_id.phone or ""), body_bold_color)

        worksheet.write(4, 5, 'Số: %s' % (self.name or ''), body_bold_color)
        worksheet.write(5, 5, 'Đơn hàng: %s'%(self.origin or self.sale_select_id.name or ''), body_bold_color)

        row = 10
        count = 0
        summary_header = ['STT', 'Mã hàng', 'Tên hàng', 'Đơn vị', 'Số lượng', 'Đơn giá', 'Thành tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_border_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]
        no = 0
        total = 0
        for line in self.move_lines:
            no += 1
            row += 1
            count += 1
            worksheet.write(row, 0, no, body_bold_border_color)
            worksheet.write(row, 1, line.product_id.default_code, body_bold_border_color)
            worksheet.write(row, 2, line.product_id.name, body_bold_border_color)
            worksheet.write(row, 3, line.product_id.uom_id.name, body_bold_border_color)
            worksheet.write(row, 4, '{0:,.2f}'.format(line.product_uom_qty), money)
            # .replace(',', ' ').replace('.', ',').replace(' ', '.')
            worksheet.write(row, 5, line.price_unit_sale, money)
            # worksheet.write(row, 5, 0, money)
            worksheet.write(row, 6, line.product_uom_qty * line.price_unit_sale, money)
            # worksheet.write(row, 6, 0, money)
            total += line.product_uom_qty * line.price_unit_sale
        row += 1
        # worksheet.merge_range('A9:F9', 'Điện thoại: %s' % (self.partner_id.phone), body_bold_color)
        worksheet.merge_range(row, 0, row, 5, unicode("Cộng", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, total, money)
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("Cộng tiền hàng", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, total, money)
        row += 1
        worksheet.merge_range(row, 0, row, 1, unicode("Thuế suất GTGT", "utf-8"), body_bold_border_color)
        worksheet.write(row, 2, '', money)
        worksheet.merge_range(row, 3, row, 5, unicode("Tiền thuế GTGT", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, '', money)
        row += 1
        worksheet.merge_range(row, 3, row, 5, unicode("Tổng thanh toán", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, total, money)
        row += 1
        string = "Số tiền viết bằng chữ: %s đồng."
        string = unicode(string, "utf-8")
        string = string % self.env['stock.picking'].DocTienBangChu(total)
        worksheet.merge_range(row, 0, row, 6, string, body_bold_color)
        row += 1
        string = "Ngày %s tháng %s năm %s" % (date.day, date.month, date.year)
        worksheet.write(row, 5, unicode(string, "utf-8"), body_bold_center_color)
        row += 2
        worksheet.merge_range(row, 0, row, 1, unicode("Người nhận hàng", "utf-8"), header_bold_color)
        worksheet.write(row, 2, unicode("Kho", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 3, row, 4, unicode("Người lập phiếu", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 5, row, 6, unicode("Giám đốc", "utf-8"), header_bold_color)
        row += 1
        worksheet.merge_range(row, 0, row, 1, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.write(row, 2, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.merge_range(row, 3, row, 4, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.merge_range(row, 5, row, 6, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'PhieuKhoExcel.xlsx', 'datas_fname': 'PhieuKhoExcel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    @api.model
    def create(self,vals):
        res = super(stock_picking, self).create(vals)
        if self.env.context.get('create_stock_out_from',False):
            self.env['stock.picking'].browse(self.env.context.get('create_stock_out_from',False)).write({'stock_out_ids': [(4,res.id)]})
        return res

    @api.multi
    def create_stock_out(self):
        for record in self:
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
            picking_obj = self.env['stock.picking']
            picking_data = picking_obj.default_get(picking_obj._fields)
            context = {}
            for key,value in picking_data.items():
                context.update({'default_' + key:value})
            location_id= False
            location_dest_id= False
            if picking_type_id:
                if picking_type_id.default_location_src_id:
                    location_id = picking_type_id.default_location_src_id.id
                else:
                    customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
                if picking_type_id.default_location_dest_id:
                    location_dest_id = picking_type_id.default_location_dest_id.id
                else:
                    location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
            context.update({
                'default_picking_type_id'   : picking_type_id.id,
                'default_location_id'       : location_id,
                'default_location_dest_id'  : location_dest_id.id,
                'default_min_date'          : str(datetime.today()),
                'default_origin'            : record.purchase_id and record.purchase_id.name or record.origin,
                # 'default_partner_id'        : record.partner_id.id or False,
                'default_shipper'           : False,
                'default_receiver'          : False,
                'create_stock_out_from'     : record.id,
            })
            move_lines = []
            move_obj = self.env['stock.move']
            for move in record.move_lines:
                line_data   = move_obj.default_get(move_obj._fields)
                line_data.update({
                    'product_id'        : move.product_id.id,
                    'name'              : move.product_id.name,
                    'product_uom_qty'   : move.product_uom_qty,
                    'product_uom'       : move.product_id.uom_id.id,
                    'procure_method'    : 'make_to_stock',
                    'warehouse_id'      : picking_type_id.warehouse_id.id,
                    'location_id'       : location_id,
                    'location_dest_id'  : location_dest_id.id,
                    'date'              : str(datetime.today()),
                    'sale_stock_out_id' : move.sale_stock_out_id.id or False
                })
                move_lines.append((0, 0, line_data))
            if move_lines:
                context.update({'default_move_lines': move_lines})
            # picking_data['move_lines'] = move_lines
            # picking_id = self.env['stock.picking'].create(picking_data)
            # record.write({'stock_out_ids': [(4,picking_id.id)]})
            # action = self.env.ref('stock.action_picking_tree_all').read()[0]
            # action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            # action['res_id'] = picking_id.id
            return {
                'type'      : 'ir.actions.act_window',
                'name'      : 'Đơn xuất',
                'view_type' : 'form',
                'view_mode' : 'form',
                'res_model' : 'stock.picking',
                'view_id'   : self.env.ref('stock.view_picking_form').id,
                'context'   : context,
            }

    @api.one
    @api.depends('move_lines.date_expected')
    def _compute_dates(self):
        if 'min_date' in self._context and self._context['min_date']:
            self.min_date = self._context['min_date']
        else:
            self.min_date = min(self.move_lines.mapped('date_expected') or [False])
        self.max_date = max(self.move_lines.mapped('date_expected') or [False])

    # create multi stock out
    @api.multi
    def create_multi_stock_out(self):
        for record in self:
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
            picking_obj = self.env['stock.picking']
            picking_data = picking_obj.default_get(picking_obj._fields)

            location_id= False
            location_dest_id= False
            if picking_type_id:
                if picking_type_id.default_location_src_id:
                    location_id = picking_type_id.default_location_src_id.id
                else:
                    customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
                if picking_type_id.default_location_dest_id:
                    location_dest_id = picking_type_id.default_location_dest_id.id
                else:
                    location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
            picking_data.update({
                'picking_type_id'   : picking_type_id.id,
                'location_id'       : location_id,
                'location_dest_id'  : location_dest_id.id,
                'min_date'          : str(datetime.today()),
                'origin'            : record.purchase_id and record.purchase_id.name or record.origin,
                # 'default_partner_id'        : record.partner_id.id or False,
                'shipper'           : False,
                'receiver'          : False,

            })

            move_obj = self.env['stock.move']
            # distinct sale_stock_out
            for sale_id in record.move_lines.mapped('sale_stock_out_id'):
                picking_val = picking_data.copy()
                move_lines = []
                for move in record.move_lines.filtered(lambda rec:rec.sale_stock_out_id and rec.sale_stock_out_id.id == sale_id.id):
                    line_data   = move_obj.default_get(move_obj._fields)
                    line_data.update({
                        'product_id'        : move.product_id.id,
                        'name'              : move.product_id.name,
                        'product_uom_qty'   : move.product_uom_qty,
                        'product_uom'       : move.product_id.uom_id.id,
                        'procure_method'    : 'make_to_stock',
                        'warehouse_id'      : picking_type_id.warehouse_id.id,
                        'location_id'       : location_id,
                        'location_dest_id'  : location_dest_id.id,
                        'date'              : str(datetime.today()),
                        'sale_stock_out_id' : move.sale_stock_out_id.id or False
                    })
                    move_lines.append((0, 0, line_data))

                if move_lines:
                    picking_val.update({'move_lines': move_lines})
                picking_obj.with_context(create_stock_out_from=record.id).create(picking_val)

            if record.move_lines.filtered(lambda rec: not rec.sale_stock_out_id):
                move_lines = []
                picking_val = picking_data.copy()
                for move in record.move_lines.filtered(lambda rec: not rec.sale_stock_out_id):
                    line_data = move_obj.default_get(move_obj._fields)
                    line_data.update({
                        'product_id'    : move.product_id.id,
                        'name'          : move.product_id.name,
                        'product_uom_qty': move.product_uom_qty,
                        'product_uom'   : move.product_id.uom_id.id,
                        'procure_method': 'make_to_stock',
                        'warehouse_id'  : picking_type_id.warehouse_id.id,
                        'location_id'   : location_id,
                        'location_dest_id': location_dest_id.id,
                        'date'          : str(datetime.today()),
                        'sale_stock_out_id': move.sale_stock_out_id.id or False
                    })
                    move_lines.append((0, 0, line_data))

                if move_lines:
                    picking_val.update({'move_lines': move_lines})
                picking_obj.with_context(create_stock_out_from=record.id).create(picking_val)

            return record.action_view_stock_out()

class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    color = fields.Char()

    @api.multi
    def write(self,vals):
        if vals.get('product_qty',False):
            if self.qty_done == vals.get('product_qty',False) and self.qty_done > self.product_qty:
                vals.update({'color' : 'red'})
        res = super(stock_pack_operation, self).write(vals)
        return res

class stock_picking_type(models.Model):
    _inherit = 'stock.picking.type'

    account_analytic_ids = fields.Many2many('account.analytic.tag',string='Tài khoản quản trị')
