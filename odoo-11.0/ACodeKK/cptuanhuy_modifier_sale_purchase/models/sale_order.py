# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64
import StringIO
from xlrd import open_workbook
from odoo.exceptions import UserError, ValidationError

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    # @api.multi
    # def _action_procurement_create(self):
    #
    #     original_route_ids = {}
    #     for record in self:
    #         if record.product_id.qty_available >= record.product_uom_qty:
    #             route_ids = record.product_id.route_ids
    #             record.product_id.route_ids = self.env.ref('purchase.route_warehouse0_buy')
    #             original_route_ids.update({
    #                 record.id: route_ids,
    #             })
    #
    #     res = super(sale_order_line, self)._action_procurement_create()
    #     if original_route_ids:
    #         for record_id in original_route_ids:
    #             route_ids = original_route_ids.get(record_id)
    #             for record in self:
    #                 if record.id == record_id:
    #                     record.product_id.route_ids = route_ids
    #
    #     return res

    @api.onchange('tax_id')
    def onchange_tax_to_tax_sub(self):
        if self.tax_id:
            tax = self.tax_id[0]
            self.tax_sub = self.tax_id[0].amount

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'price_discount')
    @api.onchange('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'price_discount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.price_discount:
                price = line.price_discount
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('product_id')
    @api.depends('product_id')
    def depends_product_to_name(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            self.name = self.product_id.name

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if self.order_id.state != 'sale':
            if not self.product_id:
                return {'domain': {'product_uom': []}}

            vals = {}
            domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
            if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
                vals['product_uom'] = self.product_id.uom_id
                vals['product_uom_qty'] = 1.0

            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=vals.get('product_uom_qty') or self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id
            )

            result = {'domain': domain}

            title = False
            message = False
            warning = {}
            if product.sale_line_warn != 'no-message':
                title = _("Warning for %s") % product.name
                message = product.sale_line_warn_msg
                warning['title'] = title
                warning['message'] = message
                result = {'warning': warning}
                if product.sale_line_warn == 'block':
                    self.product_id = False
                    return result

            name = product.name
            if product.description_sale:
                name += '\n' + product.description_sale
            vals['name'] = name
            vals['brand_name'] = product.brand_name
            vals['group_sale_id'] = product.group_sale_id and product.group_sale_id.id

            for record in self:
                if record.order_id.tax_id and record.order_id.tax_id.id:
                    record.tax_id = record.order_id.tax_id
                    record.tax_sub = int(record.order_id.tax_id.amount)

            self._compute_tax_id()

            if self.order_id.pricelist_id and self.order_id.partner_id and not self.sale_order_return:
                price_unit = self.env['account.tax']._fix_tax_included_price_company(
                    self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
                vals['price_unit'] = price_unit
            self.update(vals)

            self.onchange_product_for_ck()
            return result
        else:
            self.name = self.product_id.name
            if self.product_id.description_sale:
                self.name += '\n' + self.product_id.description_sale

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                 product.taxes_id, self.tax_id,
                                                                                 self.company_id)
            if not self.sale_order_return:
                self.price_unit = price_unit
                if self.order_partner_id:
                    self.onchange_product_for_ck(self.order_partner_id.id)

class sale_order(models.Model):
    _inherit = 'sale.order'

    manual_picking_ids   = fields.One2many('stock.picking', 'sale_select_id', string='Manual Pickings')
    manual_picking_count = fields.Integer(string='Giao Nhận', compute='_get_manual_picking_count')
    advance_payment      = fields.Float('Tạm ứng')

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            order = self.search([('name', '=', record.name), ('id', '!=', record.id)])
            if order:
                raise ValidationError(_("Tên của đơn hàng phải là duy nhất!"))


    def _get_manual_picking_count(self):
        for record in self:
            record.manual_picking_count = len(record.manual_picking_ids.ids)

    @api.multi
    def action_open_manual_picking(self):
        picking_ids       = self.manual_picking_ids # .filtered(lambda ct: ct.is_project == True)
        action            = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain']  = [('id', 'in', picking_ids.ids)]
        action['context'] = {
            'default_sale_select_id'  : self.id,
            'default_picking_type_id' : self.env.ref('stock.picking_type_out').id,
            'search_default_wh_stock' : True
        }
        return action

    @api.multi
    def import_data_excel(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)
                order_line = record.order_line.browse([])
                # row_error = []
                # for row_no in range(sheet.nrows):
                #     if row_no > 0:
                #         row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                #                    sheet.row(row_no)))
                #         product = self.env['product.product'].search([
                #             '|', ('default_code', '=', row[0].strip()),
                #             ('barcode', '=', row[0].strip())
                #         ], limit=1)
                #         if not product or int(float(row[1])) < 0:
                #             row_error.append({
                #                 'default_code': row[0],
                #                 'price': row[2] or False,
                #                 'qty': row[1],
                #             })
                # if row_error:
                #     return {
                #         'name': 'Import Warning',
                #         'type': 'ir.actions.act_window',
                #         'res_model': 'import.warning',
                #         'view_type': 'form',
                #         'view_mode': 'form',
                #         'target': 'new',
                #         'context': {
                #             'data': row_error,
                #         }
                #     }
                # else:
                for row_no in range(sheet.nrows):

                    if row_no > 0:
                        row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                        if len(row) >= 2:
                            product = self.env['product.product'].search([
                                '|', ('default_code', '=', row[0].strip()),
                                ('barcode', '=', row[0].strip())
                            ], limit=1)
                            if not product:
                                product_data = {
                                    'name': row[1].strip(),
                                    'default_code': row[0].strip(),
                                }
                                if row[2].strip():
                                    product_uom = self.env['product.uom'].search([
                                        ('name', '=', row[2].strip())
                                    ], limit=1)
                                    if product_uom:
                                        product_data.update({
                                            'uom_id': product_uom.id,
                                            'uom_po_id': product_uom.id,
                                        })
                                    else:
                                        product_uom = self.env['product.uom'].create({
                                            'name': row[2].strip(),
                                            'category_id': self.env['product.uom.categ'].search([('name', '=', 'Đơn vị')],limit=1).id

                                        })
                                        product_data.update({
                                            'uom_id': product_uom.id,
                                            'uom_po_id': product_uom.id,
                                        })

                                product = self.env['product.product'].create(product_data)

                            if product and product.id:
                                line_data = {
                                    'order_id': record.id,
                                    'product_id': product.id,
                                    'product_uom': product.uom_id.id,
                                    'price_unit': product.lst_price,
                                    'product_uom_qty': float(row[3]),
                                }
                                line = record.order_line.create(line_data)
                                line.product_id_change()
                                line.product_uom_change()
                                line.onchange_product_for_ck(self.partner_id.id)
                                if row[4] or row[4] != 0:
                                    line.price_discount = float(row[4])
                                order_line += line
                record.order_line = order_line


    @api.depends('order_line.price_total')
    def _amount_all(self):
        # return True
        for order in self:
            amount_untaxed = amount_tax = amount_discount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                if line.price_discount:
                    amount_discount += (line.product_uom_qty * (line.price_unit - line.price_discount))
                else:
                    amount_discount += (line.product_uom_qty * line.price_unit * line.discount) / 100
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_discount': order.pricelist_id.currency_id.round(amount_discount),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name:
            partner_ids = self.env['res.partner'].search([('name','ilike',name)])
            if partner_ids and len(partner_ids.ids):
                args += ['|', ('partner_id', 'in', partner_ids.ids)]

        res = super(sale_order, self.with_context(name_search_so=True)).name_search(name=name, args=args, operator=operator, limit=limit)
        return res

    @api.multi
    def check_sale_order_line_procurement(self):
        for record in self:
            order_line = []
            if record.state in ['sale','done']:
            # filter order line with product route manufacture
                for line in record.order_line:
                    if line.product_id and self.env.ref('mrp.route_warehouse0_manufacture').id in line.product_id.route_ids.ids:
                        production = self.env['mrp.production'].search([('procurement_ids', 'in', line.procurement_ids.ids)])
                        if not production and line.procurement_ids:
                            order_line.append(line.id)
            for line in order_line:
                line_id = self.env['sale.order.line'].browse(line)
                if line_id.procurement_ids:
                    line_id.procurement_ids.with_context(create_mo_from_sale=True).make_mo()

class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    def _prepare_mo_vals(self, bom):
        res = super(ProcurementOrder, self)._prepare_mo_vals(bom)
        if self.env.context.get('create_mo_from_sale',False) and self.env.ref("mrp.picking_type_manufacturing"):
            res.update({'picking_type_id'   : self.env.ref("mrp.picking_type_manufacturing").id,
                        'location_src_id'   : self.env.ref("mrp.picking_type_manufacturing").default_location_src_id.id or False,
                        'location_dest_id'  : self.env.ref("mrp.picking_type_manufacturing").default_location_dest_id.id or False
                        })
        return res