# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import StringIO
import xlsxwriter
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import base64
import StringIO
from xlrd import open_workbook


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    date_planned = fields.Datetime(string='Scheduled Date', compute=False, store=True, index=True,
                                   default=fields.Datetime.now)
    bill_amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, track_visibility='always')
    bill_amount_tax = fields.Monetary(string='Taxes (Bill Price)', store=True, readonly=True)
    bill_amount_total = fields.Monetary(string='Total (Bill Price)', store=True, readonly=True)
    order_by = fields.Many2one('res.users', string='Order By', default=lambda self: self.env.user, readonly=True,
                               copy=False)
    validate_date = fields.Datetime(string='Validate Date', copy=False)
    validate_by = fields.Many2one('res.users', string='Validate By', readonly=True, copy=False)
    send_quotation_date = fields.Datetime(string='Send Quotation Date', copy=False)
    send_quotation_by = fields.Many2one('res.users', string='Send Quotation By', readonly=True, copy=False)
    confirmation_date = fields.Datetime(string='Create Date', readonly=True, index=True, copy=False,
                                        default=fields.Datetime.now)
    total_qty = fields.Float(string='Tổng số lượng', store=True, compute='_bill_amount_all')
    bill_total_qty = fields.Float(string='Tổng số lượng', store=True, compute='_bill_amount_all')
    operation_state = fields.Selection([
        ('waiting_pick', 'Waiting to Pick'), ('ready_pick', 'Ready to Pick'), ('picking', 'Picking'),
        ('waiting_pack', 'Waiting to Pack'), ('packing', 'Packing'),
        ('waiting_delivery', 'Waiting to Delivery'), ('delivery', 'Delivering'),
        ('reveive', 'Receive'), ('waiting', 'Waiting to Check'), ('checking', 'Checking'),
        ('done', 'Done'),
        ('reverse_tranfer', 'Reverse Tranfer'),
        ('cancel', 'Cancel')
    ], string='Operation Status', )
    state_return = fields.Selection([
        ('draft', 'Purchase Return Quotation'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Return'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', index=True, copy=False)
    purchase_person = fields.Many2one('res.users', string='Purchase Person', readonly=True)
    operation_status = fields.Selection([
        ('waiting_pick', 'Waiting to Pick'), ('ready_pick', 'Ready to Pick'), ('picking', 'Picking'),
        ('waiting_pack', 'Waiting to Pack'), ('packing', 'Packing'),
        ('waiting_delivery', 'Waiting to Delivery'), ('delivery', 'Delivering'),
        ('reveive', 'Receive'), ('waiting', 'Waiting to Check'), ('checking', 'Checking'),
        ('done', 'Done'),
        ('reverse_tranfer', 'Reverse Tranfer'),
        ('cancel', 'Cancel')
    ], string='Operation Status', )
    file_name = fields.Char('File Name')
    product_line_id = fields.Char(string='Product')
    purchase_tax = fields.Selection([('0', '0%'),('5', '5%'),('10', '10%')],string='Taxes (default)')
    purchase_bill_tax = fields.Selection([('0', '0%'),('5', '5%'),('10', '10%')],string='Taxes (Bill default)', related='purchase_tax', readonly=1)

    discount_month = fields.Integer()

    @api.onchange('partner_id')
    def onchange_partner_get_tax(self):
        if self.partner_id and self.partner_id.loai_hinh_kd_id:
            self.purchase_tax = self.purchase_bill_tax = self.partner_id.loai_hinh_kd_id.tax
        else:
            self.purchase_tax = 0

    @api.onchange('purchase_tax', 'discount_month')
    def onchange_purchase_tax(self):
        if self.purchase_tax:
            purchase_tax = int(self.purchase_tax)
        else:
            purchase_tax = 0
        tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'),('amount', '=', purchase_tax)], limit=1)
        if not tax_id:
            self.purchase_tax = False
        for line in self.order_line:
            line.tax_sub = purchase_tax
            line.onchange_tax_sub()

        amount_tax = 0.0
        for line in self.order_line:
            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.partner_id)
            amount_tax += taxes['total_included'] - taxes['total_excluded']
        self.amount_tax = amount_tax
        if self.discount_month and self.purchase_tax:
            self.amount_tax = (self.amount_untaxed - self.discount_month) * float(self.purchase_tax) / 100
            self.amount_total = (self.amount_untaxed - self.discount_month) + self.amount_tax

    @api.model
    def get_product_name_report(self, product_id):
        variants = [product_id.name]
        for attr in product_id.attribute_value_ids:
            if attr.attribute_id.name in ('Size', 'size'):
                variants.append(('Size ' + attr.name))
            else:
                variants.append((attr.name))

        product_name = ' - '.join(variants)
        return product_name

    @api.multi
    def update_purchase_order(self):
        for rec in self:
            for line in rec.order_line:
                line._onchange_quantity()
                line._bill_onchange_quantity()
            rec.button_dummy()

    @api.depends('order_line.bill_price_subtotal')
    def _bill_amount_all(self):
        for order in self:
            total_qty = 0.0
            for line in order.order_line:
                total_qty += line.product_qty
            order.update({
                'total_qty': total_qty,
                'bill_total_qty': total_qty
            })

    @api.multi
    def button_confirm(self):
        if not self.order_line:
            pass
        else:
            res = super(purchase_order, self).button_confirm()
            self.validate_date = datetime.now()
            self.validate_by = self._uid
            self.confirmation_date = fields.Datetime.now()
            return res

    @api.multi
    def action_rfq_send(self):
        if not self.order_line:
            pass
        else:
            res = super(purchase_order, self).action_rfq_send()
            self.send_quotation_date = datetime.now()
            self.send_quotation_by = self._uid
            return res

    @api.onchange('date_planned')
    def onchange_date_planned(self):
        if self.date_planned:
            for line in self.order_line:
                line.date_planned = self.date_planned

    @api.depends('group_id')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                # moves = moves.filtered(lambda r: r.state != 'cancel')
                picking_ids = self.env['stock.picking'].search(
                    [('group_id', '=', order.group_id.id)]) if order.group_id else []
                pickings |= moves.mapped('picking_id')
                if picking_ids:
                    pickings |= picking_ids
            order.picking_ids = pickings
            order.picking_count = len(pickings)

    @api.multi
    def button_dummy(self):

        self.supply_rate()

        for line in self.order_line:
            if line.price_discount:
                price = line.price_discount
                taxes_id = line.taxes_id
            else:
                price = line.price_unit
                taxes_id = line.taxes_id

            taxes = taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty,
                                         product=line.product_id, partner=line.order_id.partner_id)

            taxes_bill = line.taxes_id.compute_all(line.bill_price, line.order_id.currency_id, line.product_qty,
                                                   product=line.product_id, partner=line.order_id.partner_id)
            line.write({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'bill_price_subtotal': taxes_bill['total_excluded'],
            })

        for order in self:

            bill_amount_untaxed = amount_tax = total_qty = 0.0
            for line in order.order_line:
                total_qty += line.product_qty
                bill_amount_untaxed += line.bill_price_subtotal
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.taxes_id.compute_all(line.bill_price, line.order_id.currency_id, line.product_qty,
                                                      product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax

            order.write({
                'bill_amount_untaxed': order.currency_id.round(bill_amount_untaxed),
                'bill_amount_tax': order.currency_id.round(amount_tax),
                'bill_amount_total': bill_amount_untaxed + amount_tax,
                'total_qty': total_qty,
                'bill_total_qty': total_qty
            })

            amount_untaxed = amount_tax = amount_discount = discount_month = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
                                                      product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
                if line.price_discount:
                    amount_discount += (line.product_qty * (line.price_unit - line.price_discount))
                else:
                    amount_discount += (line.product_qty * line.price_unit * line.discount) / 100
            if self.discount_month:
                amount_tax = (amount_untaxed - self.discount_month) * float(self.purchase_tax) / 100
                discount_month = self.discount_month
            else:
                pass
            order.write({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_discount': order.currency_id.round(amount_discount),
                'amount_total': amount_untaxed - discount_month + amount_tax,
                'discount_month': self.discount_month,
            })

    @api.model
    def create(self, vals):
        vals['confirmation_date'] = fields.Datetime.now()
        if "order_line" in vals.keys():
            product_list = []
            for obj in vals['order_line']:
                if obj[2]['product_id'] not in product_list:
                    product_list.append(obj[2]['product_id'])
            list_new = vals['order_line']
            new_list = []
            for obj in product_list:
                count = 0
                qty = 0
                for element in list_new:
                    if obj == element[2]['product_id']:
                        qty += element[2]['product_qty']
                for ele in list_new:
                    if obj == ele[2]['product_id']:
                        count += 1
                        if count == 1:
                            ele[2]['product_qty'] = qty
                            new_list.append(ele)
            vals['order_line'] = new_list
        res = super(purchase_order, self).create(vals)
        res.date_order = datetime.now()
        return res

    @api.multi
    def write(self, vals):
        product_list_ext = []
        product_list_new = []
        if "order_line" in vals.keys():
            new_list = vals['order_line']
            pro_list = []
            for att in new_list:
                if att[0] == 4:
                    s = self.order_line.browse(att[1])
                    if s.product_id and s.product_id.id not in product_list_ext:
                        product_list_ext.append(s.product_id.id)
                if att[0] == 1:
                    s = self.order_line.browse(att[1])
                    if s.product_id and s.product_id.id not in product_list_ext:
                        product_list_ext.append(s.product_id.id)
                if att[0] == 0:
                    if att[2]['product_id'] not in product_list_new:
                        product_list_new.append(att[2]['product_id'])
            if not product_list_ext and self.order_line:
                for line in self.order_line:
                    if line.product_id not in product_list_ext:
                        product_list_ext.append(line.product_id.id)
            for obj in product_list_new:
                pro_qty = 0
                if obj in product_list_ext:
                    for att in new_list:
                        if att[0] == 1:
                            o = self.order_line.browse(att[1])
                            if o.product_id.id == obj:
                                pro_qty += att[2].get('product_qty', False) or 1
                        if att[1] == 0:
                            if att[0] == 0:
                                if att[2]['product_id'] == obj:
                                    pro_qty += att[2].get('product_qty', False) or 1
                                    if self.order_line:
                                        for line in self.order_line:
                                            if (line.product_id and line.product_id.id == obj):
                                                pro_qty += line.product_qty

                    for att1 in new_list:
                        if att1[0] == 4:
                            o = self.order_line.browse(att1[1])
                            if o.product_id.id == obj:
                                o.product_qty = pro_qty
                                # o.product_uos_qty = pro_qty
                        if att1[0] == 1:
                            o = self.order_line.browse(att1[1])
                            if o.product_id.id == obj:
                                att1[2]['product_qty'] = pro_qty
                                o.product_qty = pro_qty
                        if att1[0] == 0 and self:
                            for line in self.order_line:
                                if line.product_id and line.product_id.id == obj:
                                    line.product_qty = pro_qty
                                    # line.product_uos_qty = pro_qty
            for obj1 in product_list_new:
                pro_qty = 0
                count = 0
                if obj1 not in product_list_ext:
                    for att1 in new_list:
                        if att1[0] == 0:
                            if att1[2]['product_id'] == obj1:
                                pro_qty += att1[2].get('product_qty', False) or 1
                    for att2 in new_list:
                        if att2[0] == 0:
                            if att2[2]['product_id'] == obj1:
                                count += 1
                                if count == 1:
                                    att2[2]['product_qty'] = pro_qty
                                    pro_list.append(att2)

            for obj2 in product_list_ext:
                if obj2 not in product_list_new:
                    for att2 in new_list:
                        if att2[0] == 4:
                            o = self.order_line.browse(att2[1])
                            if o.product_id.id == obj2:
                                pro_list.append(att2)
            for att3 in new_list:
                if att3[0] == 2:
                    pro_list.append(att3)
                if att3[0] == 1:
                    check = False
                    if att3[2].get('product_id', False):
                        for line in pro_list:
                            o = self.order_line.browse(line[1])
                            if o.product_id.id == att3[2].get('product_id'):
                                o.product_qty += att3[2].get('product_qty') or self.order_line.browse(
                                    att3[1]).product_qty
                                new_line = att3
                                new_line[0] = 2
                                pro_list.append(new_line)
                                check = True
                    if not check:
                        pro_list.append(att3)

            vals['order_line'] = pro_list
        res = super(purchase_order, self).write(vals)
        return res

    @api.model
    def search_operation_state(self, state):
        purchase_ids = self.search([]).filtered(lambda r: r.operation_state == state)
        return purchase_ids.ids

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.multi
    def import_data_excel(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)
                order_line = record.order_line.browse([])
                for row_no in range(sheet.nrows):
                    if row_no > 0:
                        row = (
                            map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                                row.value),
                                sheet.row(row_no)))
                        if row[0]:
                            product = self.env['product.product'].search([('default_code', '=', row[0].strip()), ],
                                                                         limit=1)
                            if product:
                                line_data = {
                                    'product_id': product.id,
                                    'product_uom_qty': int(float(row[1])),
                                    'product_qty': int(float(row[1])),
                                }
                                line = record.order_line.new(line_data)
                                line.onchange_product_id()
                                line._bill_onchange_quantity()
                                line.product_qty = int(float(row[1]))
                                order_line += line
                record.order_line = order_line

    # Purchase Export function

    def export_po_data_excel(self):
        if not self.purchase_order_return:
            output = StringIO.StringIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('%s' % (self.name))

            worksheet.set_column('A:A', 50)
            worksheet.set_column('B:I', 10)
            worksheet.set_column('J:K', 20)

            header_bold_color = workbook.add_format(
                {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
            header_bold_color.set_text_wrap(1)
            body_bold_color = workbook.add_format(
                {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
            body_bold_color_number = workbook.add_format(
                {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
            body_bold_color_number.set_num_format('#,##0')
            row = 0
            summary_header = ['Product', 'Measure', 'Quatity', 'Received Qty', 'Billed Qty', 'Price Unit', 'Discount',
                              'Bill Price', 'Tax', 'Subtotal', 'Bill Subtotal']

            [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
             header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

            for line in self.order_line:
                row += 1
                worksheet.write(row, 0, line.product_id.display_name or '')
                worksheet.write(row, 1, line.product_uom.name or '')
                worksheet.write(row, 2, line.product_qty or '', body_bold_color_number)
                worksheet.write(row, 3, line.qty_received, body_bold_color_number)
                worksheet.write(row, 4, line.qty_invoiced, body_bold_color_number)
                worksheet.write(row, 5, line.price_unit_sub, body_bold_color_number)
                worksheet.write(row, 6, line.discount_sub, body_bold_color_number)
                worksheet.write(row, 7, line.bill_price_sub, body_bold_color_number)
                worksheet.write(row, 8, line.tax_id_sub, body_bold_color_number)
                worksheet.write(row, 9, line.price_subtotal, body_bold_color_number)
                worksheet.write(row, 10, line.bill_price_subtotal, body_bold_color_number)

            workbook.close()
            output.seek(0)
            result = base64.b64encode(output.read())
            attachment_obj = self.env['ir.attachment']
            attachment_id = attachment_obj.create({
                'name': '%s.xlsx' % (self.name),
                'datas_fname': '%s.xlsx' % (self.name),
                'datas': result
            })
            download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            return {
                'type': 'ir.actions.act_url',
                'url': str(download_url),
            }
        else:
            output = StringIO.StringIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('%s' % (self.name))

            worksheet.set_column('A:A', 50)
            worksheet.set_column('B:C', 10)
            worksheet.set_column('D:E', 15)

            header_bold_color = workbook.add_format(
                {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
            header_bold_color.set_text_wrap(1)
            body_bold_color = workbook.add_format(
                {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
            body_bold_color_number = workbook.add_format(
                {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
            body_bold_color_number.set_num_format('#,##0')
            row = 0
            summary_header = ['Product', 'Measure', 'Quatity', 'Price Unit', 'Subtotal']

            [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
             header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

            for line in self.order_line:
                row += 1
                worksheet.write(row, 0, line.product_id.display_name or '')
                worksheet.write(row, 1, line.product_uom.name or '')
                worksheet.write(row, 2, line.product_qty or '', body_bold_color_number)
                worksheet.write(row, 3, line.price_unit, body_bold_color_number)
                worksheet.write(row, 4, line.price_subtotal, body_bold_color_number)

            workbook.close()
            output.seek(0)
            result = base64.b64encode(output.read())
            attachment_obj = self.env['ir.attachment']
            attachment_id = attachment_obj.create({
                'name': '%s.xlsx' % (self.name),
                'datas_fname': '%s.xlsx' % (self.name),
                'datas': result
            })
            download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            return {
                'type': 'ir.actions.act_url',
                'url': str(download_url),
            }

    @api.model
    def print_purchase_over(self, response, purchase=False):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        quotaion_ids = self.env['purchase.order'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)

        summary_header = ['Mã báo giá', 'Create Date', 'Vendor', 'Ghi chú', 'Sheduted Date', 'Untaxed', 'Tổng',
                          'Trạng thái đơn hàng']
        summary_header_purchase = ['Mã báo giá', 'Create Date', 'Vendor', 'Ghi chú', 'Sheduted Date', 'Untaxed',
                                   'Tổng', 'Trạng thái đơn hàng', 'Operation Status']
        summary_header_return = ['Mã trả hàng', 'Create Date', 'Vendor', 'Ghi chú', 'Untaxed', 'Tổng',
                                 'Trạng thái đơn hàng', 'Operation Status']

        row = 0
        if not purchase:
            [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

            for quotaion_id in quotaion_ids:
                row += 1
                # user_tz = self.env.user.tz or self._context.get('tz', False) or pytz.utc
                # local = pytz.timezone(user_tz)
                # date_planned = datetime.strftime(
                #     pytz.utc.localize(datetime.strptime(quotaion_id.date_planned, DT)).astimezone(local), DT)

                state = dict(self.env['purchase.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                confirmation_date = ''
                if quotaion_id.confirmation_date:
                    confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                date_planned = ''
                if quotaion_id.date_planned:
                    date_planned = self._get_datetime_utc(quotaion_id.date_planned)
                worksheet.write(row, 0, quotaion_id.name, text_style)
                worksheet.write(row, 1, confirmation_date, text_style)
                worksheet.write(row, 2, quotaion_id.partner_id.name, text_style)
                worksheet.write(row, 3, quotaion_id.notes or '', text_style)
                worksheet.write(row, 4, date_planned or '', text_style)
                worksheet.write(row, 5, quotaion_id.amount_untaxed, body_bold_color_number)
                worksheet.write(row, 6, quotaion_id.amount_total, body_bold_color_number)
                worksheet.write(row, 7, state.get(quotaion_id.state), text_style)

        elif purchase and purchase == 'purchase':

            [worksheet.write(row, header_cell, unicode(summary_header_purchase[header_cell], "utf-8"), body_bold_color)
             for

             header_cell in range(0, len(summary_header_purchase)) if summary_header_purchase[header_cell]]

            for quotaion_id in quotaion_ids:
                row += 1
                # user_tz = self.env.user.tz or self._context.get('tz', False) or pytz.utc
                # local = pytz.timezone(user_tz)
                # date_planned = datetime.strftime(
                #     pytz.utc.localize(datetime.strptime(quotaion_id.date_planned, DT)).astimezone(local), DT)

                date_planned = ''
                if quotaion_id.date_planned:
                    date_planned = self._get_datetime_utc(quotaion_id.date_planned)

                state = dict(self.env['purchase.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                operation_state = dict(
                    self.env['purchase.order'].fields_get(allfields=['operation_state'])['operation_state'][
                        'selection'])
                confirmation_date = ''
                if quotaion_id.confirmation_date:
                    confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                worksheet.write(row, 0, quotaion_id.name, text_style)
                worksheet.write(row, 1, confirmation_date, text_style)

                worksheet.write(row, 2, quotaion_id.partner_id.name, text_style)
                worksheet.write(row, 3, quotaion_id.notes or '', text_style)
                worksheet.write(row, 4, date_planned or '', text_style)
                worksheet.write(row, 5, quotaion_id.amount_untaxed, body_bold_color_number)
                worksheet.write(row, 6, quotaion_id.amount_total, body_bold_color_number)
                worksheet.write(row, 7, state.get(quotaion_id.state), text_style)
                worksheet.write(row, 8, operation_state.get(quotaion_id.operation_state), text_style)

        elif purchase and purchase == 'return':

            [worksheet.write(row, header_cell, unicode(summary_header_return[header_cell], "utf-8"), body_bold_color)
             for
             header_cell in range(0, len(summary_header_return)) if summary_header_return[header_cell]]

            for quotaion_id in quotaion_ids:
                row += 1
                state_return = dict(self.env['purchase.order'].fields_get(allfields=['state_return'])['state_return'][
                                        'selection'])
                operation_state = dict(
                    self.env['purchase.order'].fields_get(allfields=['operation_state'])['operation_state'][
                        'selection'])

                confirmation_date = ''
                if quotaion_id.confirmation_date:
                    confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                worksheet.write(row, 0, quotaion_id.name, text_style)
                worksheet.write(row, 1, confirmation_date, text_style)
                worksheet.write(row, 2, quotaion_id.partner_id.name, text_style)
                worksheet.write(row, 3, quotaion_id.notes or '', text_style)
                worksheet.write(row, 4, quotaion_id.amount_untaxed, body_bold_color_number)
                worksheet.write(row, 5, quotaion_id.amount_total, body_bold_color_number)
                worksheet.write(row, 6, state_return.get(quotaion_id.state_return), text_style)
                worksheet.write(row, 7, operation_state.get(quotaion_id.operation_state), text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_purchase_detail(self, response, purchase=False):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        quotaion_ids = self.env['purchase.order'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Detail')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:S', 20)

        attribute_list = quotaion_ids.mapped('order_line').mapped('product_id').mapped('attribute_value_ids').mapped(
            'attribute_id').mapped('name')

        summary_header = ['Mã báo giá', 'Create Date', 'Vendor', 'Ghi chú', 'Sheduted Date', 'Untaxed', 'Tổng',
                          'Mã biến thể nội bộ', 'Sản phẩm'] + attribute_list + ['Số lượng', 'Price Unit', 'Subtotal',
                                                                                'Trạng thái đơn hàng']

        summary_header_purchase = ['Mã báo giá', 'Create Date', 'Vendor', 'Ghi chú', 'Sheduted Date', 'Untaxed',
                                   'Tổng',
                                   'Mã biến thể nội bộ', 'Sản phẩm'] + attribute_list + ['Số lượng', 'Price Unit',
                                                                                         'Subtotal',
                                                                                         'Trạng thái đơn hàng',
                                                                                         'Operation Status']

        summary_header_return = ['Mã trả hàng', 'Create Date', 'Vendor', 'Ghi chú', 'Source Document', 'Untaxed',
                                 'Tổng',
                                 'Mã biến thể nội bộ', 'Sản phẩm'] + attribute_list + ['Số lượng', 'Price Unit',
                                                                                       'Subtotal',
                                                                                       'Trạng thái đơn hàng']

        row = 0
        if not purchase:
            [worksheet.write(row, header_cell, unicode(str(summary_header[header_cell]), "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

            for quotaion_id in quotaion_ids:
                state = dict(self.env['purchase.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                for line in quotaion_id.order_line:
                    thuoc_tinh_list = []
                    for attribute in attribute_list:
                        check = False
                        for product_attribute in line.product_id.attribute_value_ids:
                            if attribute == product_attribute.attribute_id.name:
                                thuoc_tinh_list.append(product_attribute.name)
                                check = True
                                break
                        if not check:
                            thuoc_tinh_list.append('')
                    confirmation_date = ''
                    if quotaion_id.confirmation_date:
                        confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                    date_planned = ''
                    if quotaion_id.date_planned:
                        date_planned = self._get_datetime_utc(quotaion_id.date_planned)
                    row += 1
                    col = 8
                    worksheet.write(row, 0, quotaion_id.name, text_style)
                    worksheet.write(row, 1, confirmation_date, text_style)
                    worksheet.write(row, 2, quotaion_id.partner_id.name, text_style)
                    worksheet.write(row, 3, quotaion_id.notes or '', text_style)
                    worksheet.write(row, 4, date_planned or '', text_style)
                    worksheet.write(row, 5, quotaion_id.amount_untaxed, body_bold_color_number)
                    worksheet.write(row, 6, quotaion_id.amount_total, body_bold_color_number)
                    worksheet.write(row, 7, line.product_id.default_code or '', text_style)
                    worksheet.write(row, 8, line.product_id.name or '', text_style)
                    for thuoc_tinh in thuoc_tinh_list:
                        col += 1
                        worksheet.write(row, col, thuoc_tinh or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.product_qty or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.price_unit or '', body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, line.price_total, body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, state.get(quotaion_id.state), text_style)

        elif purchase and purchase == 'purchase':
            [worksheet.write(row, header_cell, unicode(str(summary_header_purchase[header_cell]), "utf-8"),
                             body_bold_color)
             for

             header_cell in range(0, len(summary_header_purchase)) if summary_header_purchase[header_cell]]

            for quotaion_id in quotaion_ids:
                state = dict(self.env['purchase.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                operation_state = dict(
                    self.env['purchase.order'].fields_get(allfields=['operation_state'])['operation_state'][
                        'selection'])
                for line in quotaion_id.order_line:
                    thuoc_tinh_list = []
                    for attribute in attribute_list:
                        check = False
                        for product_attribute in line.product_id.attribute_value_ids:
                            if attribute == product_attribute.attribute_id.name:
                                thuoc_tinh_list.append(product_attribute.name)
                                check = True
                                break
                        if not check:
                            thuoc_tinh_list.append('')
                    confirmation_date = ''
                    if quotaion_id.confirmation_date:
                        confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                    date_planned = ''
                    if quotaion_id.date_planned:
                        date_planned = self._get_datetime_utc(quotaion_id.date_planned)
                    row += 1
                    col = 8
                    worksheet.write(row, 0, quotaion_id.name, text_style)
                    worksheet.write(row, 1, confirmation_date, text_style)
                    worksheet.write(row, 2, quotaion_id.partner_id.name, text_style)
                    worksheet.write(row, 3, quotaion_id.notes or '', text_style)
                    worksheet.write(row, 4, date_planned or '', text_style)
                    worksheet.write(row, 5, quotaion_id.amount_untaxed, body_bold_color_number)
                    worksheet.write(row, 6, quotaion_id.amount_total, body_bold_color_number)
                    worksheet.write(row, 7, line.product_id.default_code or '', text_style)
                    worksheet.write(row, 8, line.product_id.name or '', text_style)
                    for thuoc_tinh in thuoc_tinh_list:
                        col += 1
                        worksheet.write(row, col, thuoc_tinh or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.product_qty or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.price_unit or '', body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, line.price_total, body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, state.get(quotaion_id.state), text_style)
                    col += 1
                    worksheet.write(row, col, operation_state.get(quotaion_id.operation_state), text_style)

        elif purchase and purchase == 'return':
            [worksheet.write(row, header_cell, unicode(str(summary_header_return[header_cell]), "utf-8"),
                             body_bold_color)
             for
             header_cell in range(0, len(summary_header_return)) if summary_header_return[header_cell]]

            for quotaion_id in quotaion_ids:
                state_return = dict(self.env['purchase.order'].fields_get(allfields=['state_return'])['state_return'][
                                        'selection'])

                for line in quotaion_id.order_line:
                    thuoc_tinh_list = []
                    for attribute in attribute_list:
                        check = False
                        for product_attribute in line.product_id.attribute_value_ids:
                            if attribute == product_attribute.attribute_id.name:
                                thuoc_tinh_list.append(product_attribute.name)
                                check = True
                                break
                        if not check:
                            thuoc_tinh_list.append('')
                    confirmation_date = ''
                    if quotaion_id.confirmation_date:
                        confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                    row += 1
                    col = 8
                    worksheet.write(row, 0, quotaion_id.name, text_style)
                    worksheet.write(row, 1, confirmation_date or '', text_style)
                    worksheet.write(row, 2, quotaion_id.partner_id.name, text_style)
                    worksheet.write(row, 3, quotaion_id.notes or '', text_style)
                    worksheet.write(row, 4, quotaion_id.origin or '', text_style)
                    worksheet.write(row, 5, quotaion_id.amount_untaxed, body_bold_color_number)
                    worksheet.write(row, 6, quotaion_id.amount_total, body_bold_color_number)
                    worksheet.write(row, 7, line.product_id.default_code or '', text_style)
                    worksheet.write(row, 8, line.product_id.name or '', text_style)
                    for thuoc_tinh in thuoc_tinh_list:
                        col += 1
                        worksheet.write(row, col, thuoc_tinh or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.product_qty or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.price_unit or '', body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, line.price_total, body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, state_return.get(quotaion_id.state_return), text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
