# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from lxml import etree

class purchase_order_inherit(models.Model):
    _inherit = 'purchase.order'

    purchase_order_return = fields.Boolean()
    purchase_order_return_id = fields.Many2one('purchase.order',string="Purchase Order", track_visibility='onchange', domain=[('purchase_order_return','=',False)])
    check_show_button_return = fields.Boolean(compute="_check_show_button_return")

    def _check_show_button_return(self):
        for record in self:
            if (record.picking_ids.filtered(lambda p: p.state != 'cancel') and record.invoice_ids.filtered(
                    lambda inv: inv.state != 'cancel')) or record.state == 'cancel':
                record.check_show_button_return = True
            else:
                record.check_show_button_return = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(purchase_order_inherit, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and 'purchase_order_return' in self._context:
            doc = etree.XML(result['arch'])
            if doc.xpath("//form/header/button"):
                nodes = doc.xpath("//form/header/button")
                for node in nodes:
                    if node.attrib.get('string') not in ['In','Hủy'] and node.attrib.get('name') != 'button_action_return' and node.attrib.get('name') != 'button_draft' \
                            and node.attrib.get('name') != 'print_excel' and node.attrib.get('name') != 'action_sale_cancel':
                        node.set('invisible', '1')
                        node.set('modifiers', """{"invisible": "true"}""")
            result['arch'] = etree.tostring(doc)
        if view_type in ['form','tree'] and 'purchase_order_return' in self._context and result.get('toolbar', False) and 'action' in result['toolbar']:
            action_ids = result['toolbar'].get('action',False)
            action_remove_ids = []
            for action_id in action_ids:
                if action_id.get('xml_id') in ['action_multi_create_picking_record','action_multi_update_stock_record','tuanhuy_purchase.action_multi_create_invoice_record']:
                    action_remove_ids.append(action_id)
            for action_remove_id in action_remove_ids:
                result['toolbar'].get('action', False).remove(action_remove_id)
        return result

    @api.model
    def default_get(self, fields):
        res = super(purchase_order_inherit, self).default_get(fields)
        if 'purchase_order_return' in self._context:
            res['purchase_order_return'] = True
        return res

    @api.onchange('purchase_order_return_id')
    def onchange_purchase_order_return_id(self):
        if self.purchase_order_return_id:
            self.partner_id = self.purchase_order_return_id.partner_id

    def create_invoice_return(self):
        invoice_id = self.env['account.invoice'].create({
            'type' : 'in_refund',
            'origin': self.name,
            'partner_id' : self.partner_id.id,
            'date_invoice': self.date_order,
            # 'date_due': self.date_order,
            'date': self.date_order,
            'date_order' : self.date_order,
        })

        invoice_line = []
        account_id = self.env['account.account'].search([('code', '=', '3388')], limit=1).id or False
        for line in self.order_line:
            if line.product_id or line.quantity != 0:
                invoice_line.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.product_qty,
                    'uom_id': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'price_discount': line.price_discount,
                    'discount': line.discount,
                    'invoice_line_tax_ids': [(6,0,line.taxes_id.ids)],
                    'name': line.product_id.display_name,
                    'account_id' : line.product_id.categ_id.property_account_expense_categ_id.id or account_id,
                    'purchase_line_id' : line.id,
                }))

        invoice_id.with_context(journal_id=1).write({'invoice_line_ids': invoice_line})
        invoice_id.compute_taxes()
        return invoice_id

    def button_action_return(self):
        self.state = 'purchase'

        if not self.picking_ids.filtered(lambda p:p.state != 'cancel'):
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)

            location_id = False
            location_dest_id = False
            if picking_type_id:
                if picking_type_id.default_location_src_id:
                    location_id = picking_type_id.default_location_src_id.id
                elif self.partner_id:
                    location_id = self.partner_id.property_stock_supplier.id
                else:
                    customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

                if picking_type_id.default_location_dest_id:
                    location_dest_id = picking_type_id.default_location_dest_id.id
                elif self.partner_id:
                    location_dest_id = self.partner_id.property_stock_supplier.id
                else:
                    location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

            picking_id = self.env['stock.picking'].create({
                'picking_type_id': picking_type_id.id,
                'partner_id': self.partner_id.id,
                'origin': self.name,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'check_return_picking' : True,
                'min_date': self.date_order,
            })

            picking_line = []
            for line in self.order_line:
                if line.product_id or line.quantity != 0:
                    if self.purchase_order_return_id and self.purchase_order_return_id.picking_ids:
                        stock_move = self.purchase_order_return_id.mapped('picking_ids').mapped('move_lines').filtered(
                            lambda ml: ml.product_id == line.product_id)
                        stock_quants = stock_move.mapped('quant_ids').filtered(lambda q: q.location_id.name == 'Stock')
                        qty = sum(stock_quants.mapped('qty'))
                        if qty < line.product_qty:
                            raise UserError('Không đủ hàng để trả')

                    picking_line.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': location_id,
                        'picking_type_id': picking_type_id.id,
                        'warehouse_id': picking_type_id.warehouse_id.id,
                        'location_dest_id': location_dest_id,
                        'name': line.product_id.display_name,
                        'purchase_line_id' : line.id,
                        'procure_method': 'make_to_stock',
                        'origin': self.name,
                        'price_unit' :  line.price_discount or line.price_unit * (1 - (line.discount or 0.0) / 100.0) or 0,
                        'date': self.date_order,
                    }))

            picking_id.write({'move_lines': picking_line})

            for line in self.order_line:
                purchase_line = picking_id.move_lines.filtered(lambda l: line.id == l.purchase_line_id.id).ids or []
                line.move_ids = [(6,0,purchase_line)]

            picking_id.action_confirm()
            picking_id.action_assign()
            # if picking_id.state == 'assigned':
            #     stock_transfer_obj = self.env['stock.immediate.transfer']
            #     stock_transfer_obj.create(stock_transfer_obj.with_context({
            #         'active_id': picking_id.id
            #     }).default_get(stock_transfer_obj._fields)).process()
            picking_id.min_date = self.date_order

        # else:
        #     return {
        #         'warning': {
        #             'title': _('Cảnh báo!'),
        #             'message': _('Hàng không có sẵn trả lại'),
        #         }
        #     }

        if not self.invoice_ids.filtered(lambda inv:inv.state != 'cancel'):
            invoice_id = self.create_invoice_return()

            for line in self.order_line:
                invoice_lines = invoice_id.invoice_line_ids.filtered(lambda l: line.id == l.purchase_line_id.id).ids or []
                line.invoice_lines = [(6,0,invoice_lines)]

            invoice_id.action_invoice_open()

    @api.model
    def create(self, vals):
        result = super(purchase_order_inherit, self).create(vals)
        if result.purchase_order_return == True:
            result.name = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'purchase.order.return') or _('New')
        return result

    def on_barcode_scanned(self, barcode):
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if not product:
            product_ids = self.env['product.barcode'].search([('name', '=', barcode)]).product_id.ids
            product = self.env['product.template'].search([('id', 'in', product_ids)], limit=1).product_variant_id
        if product:
            corresponding_line = self.order_line.filtered(lambda r: r.product_id.barcode == barcode or barcode in r.product_id.barcode_ids.mapped('name'))
            if corresponding_line:
                corresponding_line[0].product_qty += 1
            else:
                line = self.order_line.new({
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    'product_qty': 1.0,
                    'price_unit': product.standard_price,
                    'date_planned': fields.Datetime.now(),
                })
                line.onchange_product_id()
                if self.purchase_order_return:
                    line.onchange_product_id_for_return(self.purchase_order_return_id.ids)
                if self.tax_id:
                    line.taxes_id = [(6, 0, self.tax_id.ids)]
                    line.tax_sub= self.tax_id.amount
                self.order_line += line
            return
        else:
            raise ValidationError(_("Không tìm thấy sản phẩm với mã barcode này."))

class purchase_order_line_inherit(models.Model):
    _inherit = 'purchase.order.line'

    purchase_order_return = fields.Boolean(compute="get_purchase_order_return", store=False)

    @api.multi
    def get_purchase_order_return(self):
        for rec in self:
            if rec.order_id:
                rec.purchase_order_return = rec.purchase_order_return

    @api.onchange('product_id')
    def onchange_product_id_for_return(self,purchase_order=None):
        if ('purchase_order_ctx' in self._context and self._context.get('purchase_order_ctx')) or purchase_order:
            if 'purchase_order_ctx' in self._context:
                purchase_id = self.env['purchase.order'].browse(self._context.get('purchase_order_ctx'))
            elif purchase_order:
                purchase_id = self.env['purchase.order'].browse(purchase_order)
            if not self.product_id:
                return {'domain': {
                    'product_id': [('id', 'in', purchase_id.mapped('order_line').mapped('product_id').ids)]}}
            else:
                purchase_line = purchase_id.order_line.filtered(lambda l: l.product_id.id == self.product_id.id)
                if purchase_line:
                    purchase_line = purchase_line[0]
                    self.product_qty = purchase_line.product_qty
                    self.price_unit = purchase_line.price_unit
                    self.tax_sub = purchase_line.tax_sub
                    self.discount = purchase_line.discount
                    self.price_discount = purchase_line.price_discount
