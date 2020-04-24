# -*- coding: utf-8 -*-

from odoo import models, fields, api
import StringIO
import xlsxwriter
from odoo.addons import decimal_precision as dp
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class product_product_ihr(models.Model):
    _inherit = 'product.product'

    sp_ban_chua_giao = fields.Integer(compute='_compute_product')
    sp_da_bao_gia = fields.Integer(compute='_compute_product')
    sp_co_the_ban = fields.Integer(compute='_compute_product')
    product_variant_price = fields.Float(string='Product Price')
    default_code = fields.Char(readonly=True)
    product_stock_move_open = fields.One2many('stock.move', 'product_id', compute='get_pp_stock_move_open')
    archived_date = fields.Datetime('Archived Time')
    unarchived_date = fields.Datetime('UnArchived Time')

    @api.multi
    def toggle_active(self):
        res = super(product_product_ihr, self).toggle_active()
        for record in self:
            if record.active == True:
                record.unarchived_date = datetime.today()
            else:
                record.archived_date = datetime.today()
        return res



    @api.multi
    def update_archived_date(self):
        for product in self.search([('active', '=', False), ('archived_date', '=', False)]):
            stock_location = self.env.ref('stock.stock_location_stock').id
            stock_location_customers = self.env.ref('stock.stock_location_customers').id
            stock_location_scrapped = self.env.ref('stock.stock_location_scrapped').id
            location_inventory = self.env.ref('stock.location_inventory').id
            stock_location_suppliers = self.env.ref('stock.stock_location_suppliers').id
            not_sellable = self.env['stock.location'].search([('not_sellable', '=', True)])
            location_dest_list = [stock_location, stock_location_customers, stock_location_scrapped, location_inventory,
                                  stock_location_suppliers] + not_sellable.ids
            moves = self.env['stock.move'].search(
                [('state', '=', 'done'), ('product_id', '=', product.id),
                 ('location_dest_id', 'in', location_dest_list)], order="date DESC")
            move_id = moves.filtered(lambda m: m.remain_qty == 0)
            if move_id:
                date = datetime.strptime(move_id[0].date, DEFAULT_SERVER_DATETIME_FORMAT)
                value = date + relativedelta(days=1)
                product.archived_date = value

    @api.multi
    def get_pp_stock_move_open(self):
        for record in self:
            stock_location = self.env.ref('stock.stock_location_stock').id
            stock_location_customers = self.env.ref('stock.stock_location_customers').id
            stock_location_scrapped = self.env.ref('stock.stock_location_scrapped').id
            location_inventory = self.env.ref('stock.location_inventory').id
            stock_location_suppliers = self.env.ref('stock.stock_location_suppliers').id
            not_sellable = self.env['stock.location'].search([('not_sellable', '=', True)])
            location_dest_list = [stock_location, stock_location_customers, stock_location_scrapped, location_inventory,
                                  stock_location_suppliers] + not_sellable.ids
            moves = self.env['stock.move'].search(
                [('state', '=', 'done'), ('product_id', '=', record.id),
                 ('location_dest_id', 'in', location_dest_list)])

            moves_return = self.env['stock.move'].search([('id', 'in', moves.ids), ('picking_id.is_picking_return', '=', True)])

            moves = moves - moves_return

            record.product_stock_move_open = moves

    def _compute_product_price(self):
        res = super(product_product_ihr, self)._compute_product_price()
        for product in self:
            product.price = product.lst_price

    @api.model
    def create(self, val):
        domain = [('default_code', '!=', False),'|',('active', '=', False),('active', '=', True)]
        if self._context.get('variants_to_unlink', False):
            domain.append(('id', 'not in', self._context.get('variants_to_unlink', False)))
        product_id = self.env['product.product'].search(domain, limit=1, order='default_code DESC')
        if not product_id:
            number_next = 1
        else:
            number_next = int(product_id.default_code.split('SPV')[1]) + 1
        val['default_code'] = 'SPV' + '{0:06}'.format(number_next)
        val['unarchived_date'] = datetime.today()
        res = super(product_product_ihr, self).create(val)
        return res

    @api.multi
    def write(self, val):
        if val.get('default_code', False) and self._context.get('write_template', False):
            del val['default_code']
        if 'active' in val:
            if val.get('active') == True:
                val.update({
                    'unarchived_date': datetime.today()
                })
            else:
                for record in self:
                    moves = record.product_stock_move_open.sorted(key=lambda r: r.date, reverse=True)
                    if moves and moves[0].remain_qty > 0:
                        raise UserError('Không thể Unactive Sản phẩm %s khi số lượng tồn kho là %s.' % (record.display_name, moves[0].remain_qty))
                val.update({
                    'archived_date': datetime.today()
                })
        res = super(product_product_ihr, self).write(val)
        return res

    # @api.depends('product_variant_price','list_price', 'price_extra')
    # def _compute_product_lst_price(self):
    #     to_uom = None
    #     if 'uom' in self._context:
    #         to_uom = self.env['product.uom'].browse([self._context['uom']])
    #
    #     for product in self:
    #         if product.product_variant_price:
    #             product.lst_price = product.product_variant_price
    #         else:
    #             if to_uom:
    #                 list_price = product.uom_id._compute_price(product.list_price, to_uom)
    #             else:
    #                 list_price = product.list_price
    #             product.lst_price = list_price + product.price_extra

    @api.multi
    def name_get(self):
        if 'product_show_onhand' in self._context:
            result = []
            for record in self:
                variable_attributes = record.attribute_line_ids.filtered(lambda l: len(l.value_ids) >= 1).mapped(
                    'attribute_id')
                variant = record.attribute_value_ids._variant_name(variable_attributes)
                name = variant and "%s (%s)" % (record.name, variant) or record.name
                result.append((record.id, "[%s] - [%s, %s] - %s" % (
                    record.default_code, record.sp_da_bao_gia + record.sp_co_the_ban, record.sp_co_the_ban, name)))
            return result
        else:
            def _name_get(d):
                name = d.get('name', '')
                code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
                if code:
                    name = '[%s] %s' % (code, name)
                return (d['id'], name)

            partner_id = self._context.get('partner_id')
            if partner_id:
                partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
            else:
                partner_ids = []

            # all user don't have access to seller and partner
            # check access and use superuser
            self.check_access_rights("read")
            self.check_access_rule("read")

            result = []
            for product in self.sudo():
                # display only the attributes with multiple possible values on the template
                variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) >= 1).mapped(
                    'attribute_id')
                variant = product.attribute_value_ids._variant_name(variable_attributes)

                name = variant and "%s (%s)" % (product.name, variant) or product.name
                sellers = []
                if partner_ids:
                    sellers = [x for x in product.seller_ids if
                               (x.name.id in partner_ids) and (x.product_id == product)]
                    if not sellers:
                        sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
                if sellers:
                    for s in sellers:
                        seller_variant = s.product_name and (
                            variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                        mydict = {
                            'id': product.id,
                            'name': seller_variant or name,
                            'default_code': s.product_code or product.default_code,
                        }
                        temp = _name_get(mydict)
                        if temp not in result:
                            result.append(temp)
                else:
                    mydict = {
                        'id': product.id,
                        'name': name,
                        'default_code': product.default_code,
                    }
                    result.append(_name_get(mydict))
            return result

    @api.depends('qty_available', 'virtual_available')
    def _compute_product(self):
        move_obj = self.env['stock.move'].sudo()
        dest_location = self.env.ref('stock.stock_location_customers')
        for rec in self:
            if self._context.get('location', False):
                sp_ban_chua_giao = sum(move_obj.search(
                    [('product_id', '=', rec.id), ('location_id', '=', self._context.get('location', False)),
                     ('state', 'not in', ['done', 'cancel'])]).mapped('product_uom_qty'))
                move_cancel_ids = move_obj.search(
                    [('product_id', '=', rec.id), ('location_id', '=', self._context.get('location', False)),
                     ('state', '=', 'cancel')])
            else:
                sp_ban_chua_giao = sum(move_obj.search(
                    [('product_id', '=', rec.id), ('location_dest_id', '=', dest_location.id or False),
                     ('state', 'not in', ['done', 'cancel'])]).mapped('product_uom_qty'))
                move_cancel_ids = move_obj.search(
                    [('product_id', '=', rec.id), ('location_dest_id', '=', dest_location.id or False),
                     ('state', '=', 'cancel')])
            sp_ban_da_huy = 0
            for move_cancel_id in move_cancel_ids:
                if move_cancel_id.picking_id.sale_id and move_cancel_id.picking_id.sale_id.trang_thai_dh == 'reverse_tranfer':
                    sp_ban_da_huy += move_cancel_id.product_uom_qty
                if move_cancel_id.picking_id.purchase_id and move_cancel_id.picking_id.purchase_id.operation_state == 'reverse_tranfer':
                    sp_ban_da_huy += move_cancel_id.product_uom_qty

            rec.sp_ban_chua_giao = sp_ban_chua_giao + sp_ban_da_huy

            line_ids = self.env['sale.order.line'].search(
                [('product_id', '=', rec.id), ('order_id.state', 'in', ('draft', 'sent'))])
            line_purchase_ids = self.env['purchase.order.line'].search(
                [('product_id', '=', rec.id), ('order_id.state', 'in', ('draft', 'sent')),
                 ('order_id.purchase_order_return', '=', True)])
            sp_da_bao_gia = sum(line_ids.mapped('product_uom_qty')) + sum(line_purchase_ids.mapped('product_qty'))
            rec.sp_da_bao_gia = sp_da_bao_gia
            rec.sp_co_the_ban = rec.qty_available - rec.sp_ban_chua_giao - rec.sp_da_bao_gia

    @api.model
    def get_categ_list(self):
        categ_ids = self.env['product.category'].search([]).sorted('display_name', reverse=False).with_context(
            {'lang': self.env.user.lang or 'vi_VN'}).mapped('display_name')
        categ_list = []
        for categ_id in categ_ids:
            categ_list.append(categ_id.replace("/", ">>"))
        return categ_list

    @api.model
    def get_categ_name_search(self, categ_name):
        if categ_name:
            categ_list = categ_name.split('>>')
            parent_id = False
            for categ in categ_list:
                domain = [('name', '=', categ.strip())]
                if not parent_id:
                    categ_id = self.env['product.category'].search(domain)
                    if not categ_id:
                        break
                    parent_id = categ_id
                else:
                    domain.append(('parent_id', '=', parent_id.id))
                    categ_id = self.env['product.category'].search(domain)
                    if not categ_id:
                        break
                    parent_id = categ_id

            if parent_id:
                product_ids = self.env['product.product'].search([('categ_id', '=', parent_id.id)])
                return product_ids.ids
            else:
                return []

    def check_group_show_cost(self):
        if self.env.user.has_group('tts_modifier_access_right.group_giam_doc_kd') or self.env.user.has_group(
                'tts_modifier_access_right.group_nv_nganh_hang') or \
                self.env.user.has_group('tts_modifier_access_right.group_nv_mua_hang') or self.env.user.has_group(
            'tts_modifier_access_right.group_ketoan_tonghop') or \
                self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho'):
            return True
        else:
            return False

    @api.model
    def print_product_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        product_ids = self.env['product.product'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Biến thể sản phẩm')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)
        attribute_list = product_ids.mapped('attribute_value_ids').mapped('attribute_id').mapped('name')
        if self.check_group_show_cost():
            summary_header = ['Nhóm sản phẩm', 'Mã biến thể (variant)', 'Tên sản phẩm'] + attribute_list + [
                'Giá bán', 'Giá vốn',
                'SL tổng TK', 'SL bán chưa giao', 'SL đã báo giá', 'SL có thể bán']
        else:
            summary_header = ['Nhóm sản phẩm', 'Mã biến thể (variant)', 'Tên sản phẩm'] + attribute_list + [
                'Giá bán', 'SL tổng TK', 'SL bán chưa giao', 'SL đã báo giá', 'SL có thể bán']

        row = 0
        [worksheet.write(row, header_cell, unicode(str(summary_header[header_cell]), "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for product_id in product_ids:
            row += 1
            # thuoc_tinh_1 = ''
            # thuoc_tinh_2 = ''
            # if len(product_id.attribute_value_ids) >= 1:
            #     thuoc_tinh_1 = product_id.attribute_value_ids[0].display_name
            # if len(product_id.attribute_value_ids) >= 2:
            #     thuoc_tinh_2 = product_id.attribute_value_ids[1].display_name
            thuoc_tinh_list = []
            for attribute in attribute_list:
                check = False
                for product_attribute in product_id.attribute_value_ids:
                    if attribute == product_attribute.attribute_id.name:
                        thuoc_tinh_list.append(product_attribute.name)
                        check = True
                        break
                if not check:
                    thuoc_tinh_list.append('')
            col = 2
            worksheet.write(row, 0, product_id.categ_id.display_name.replace("/", ">>"), text_style)
            worksheet.write(row, 1, product_id.default_code if product_id.default_code else '', text_style)
            worksheet.write(row, 2, product_id.name, text_style)
            # worksheet.write(row, 3, thuoc_tinh_1, text_style)
            # worksheet.write(row, 4, thuoc_tinh_2, text_style)
            for thuoc_tinh in thuoc_tinh_list:
                col += 1
                worksheet.write(row, col, thuoc_tinh or '', text_style)
            col += 1
            worksheet.write(row, col, product_id.lst_price, body_bold_color_number)
            if self.check_group_show_cost():
                col += 1
                worksheet.write(row, col, product_id.standard_price, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.qty_available, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.sp_ban_chua_giao, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.sp_da_bao_gia, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.sp_co_the_ban, body_bold_color_number)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


class ProductAttributevalue(models.Model):
    _inherit = "product.attribute.value"
    _order = 'attribute_id, name'

    @api.multi
    def name_get(self):
        return [(value.id, "%s" % (value.name)) for value in self]


class StockMoveIhr(models.Model):
    _inherit = "stock.move"
    _order = 'date desc'

    invoices_bill = fields.Char(string="Invoices/Vendor Bills", compute="get_invoice_bill", store=False)
    origin_sub = fields.Char(string="Source Document", compute="get_move_origin_sub", store=False)
    product_uom_qty_sub = fields.Float(
        'Quantity',
        digits=dp.get_precision('Product Unit of Measure'), compute="get_product_uom_qty_sub", store=False)
    partner = fields.Char(string="Partners", compute='ref_user')

    @api.depends('origin', 'inventory_id')
    def get_move_origin_sub(self):
        for record in self:
            if record.inventory_id:
                record.origin_sub = record.inventory_id.name
            else:
                record.origin_sub = record.origin

    @api.multi
    def get_invoice_bill(self):
        for record in self:
            if record.origin:
                invoice_ids = self.env['account.invoice'].search([('origin', '=', record.origin)])
                record.invoices_bill = ', '.join(invoice_ids.mapped('display_name'))

    @api.multi
    def get_product_uom_qty_sub(self):
        for record in self:
            record.product_uom_qty_sub = record.quantity_in or -record.quantity_out or 0

    @api.multi
    def ref_user(self):
        for rec in self:
            rec.partner = rec.picking_id.partner_id.name
