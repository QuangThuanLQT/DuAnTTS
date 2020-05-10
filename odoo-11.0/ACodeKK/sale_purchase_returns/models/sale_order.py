# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from lxml import etree
from dateutil.relativedelta import relativedelta

class StockMove(models.Model):
    _inherit = 'stock.move'

    return_quant_id = fields.Many2one('stock.quant', 'Return Quant')

class StockQuantReturn(models.Model):
    _inherit = 'stock.quant'

    order_ref = fields.Many2one('sale.order', 'Origin')


class ReturnPicking(models.Model):
    _inherit = 'stock.picking'

    check_return_picking = fields.Boolean(default=False)

    def compare_order(self, rtrn_order, order, product_id):
        rtrn_qties = rtrn_order.mapped('order_line').filtered(lambda line: line.product_id == product_id).mapped('product_uom_qty')
        qties = order.mapped('order_line').filtered(lambda line: line.product_id == product_id).mapped('product_uom_qty')
        return sum(rtrn_qties) <= sum(qties)

    @api.multi
    def action_assign(self):
        if self.env.context.get('sale_order_return', False):
            for record in self:
                return_order = self.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                if return_order and not return_order.sale_order_return_ids:
                    moves = record.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
                    for move in moves:
                        quant = self.env['stock.quant'].create({
                            'product_id': move.product_id.id,
                            'location_id': move.location_id.id,
                            'qty': move.product_uom_qty,
                            'cost': move.product_id.standard_price,
                            'inventory_value': move.product_id.standard_price*move.product_uom_qty,
                            'reservation_id': False,
                            'order_ref': return_order.id,
                            'in_date': '2018-08-31',
                        })
                        move.return_quant_id = quant
                        move.state = 'assigned'
                    record.state = 'assigned'
                    return True
                else:
                    moves = record.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
                    old_moves = self.env['stock.move']
                    for order in return_order.sale_order_return_ids:
                        for picking_id in order.picking_ids:
                            for stock_move in picking_id.move_lines:
                                old_moves |= stock_move

                    for move in moves:
                        my_moves = old_moves.filtered(lambda x: x.product_id == move.product_id)
                        qty, cost  = 0, 0
                        for my_move in my_moves:
                            qty += sum(my_move.quant_ids.mapped('qty'))
                            cost += sum(my_move.quant_ids.mapped('inventory_value'))
                        if qty == 0:
                            raise UserError('Sản phẩm %s chưa được xuất kho trong đơn hàng cũ' % (move.product_id.name))

                        quant = self.env['stock.quant'].create({
                            'product_id': move.product_id.id,
                            'location_id': move.location_id.id,
                            'qty': move.product_uom_qty,
                            'cost': cost / qty,
                            'inventory_value': move.product_uom_qty*cost/qty,
                            'reservation_id': False,
                            'order_ref': return_order.id,
                            'in_date': '2018-08-31',
                        })
                        move.return_quant_id = quant
                        move.state = 'assigned'
                    record.state = 'assigned'
                    return True

        return super(ReturnPicking, self).action_assign()

    @api.multi
    def do_new_transfer(self):
        for record in self:
            moves = record.mapped('move_lines').filtered(
                lambda move: move.state not in ('draft', 'cancel', 'done'))
            for move in moves:
                if move.return_quant_id:
                    self.env['stock.quant'].search([
                        ('reservation_id', '=', move.id)
                    ]).write({
                        'reservation_id': False,
                    })
                    move.return_quant_id.reservation_id = move.id
        super(ReturnPicking, self).do_new_transfer()


class sale_order_inherit(models.Model):
    _inherit = 'sale.order'

    sale_order_return = fields.Boolean()
    sale_order_return_id = fields.Many2one('sale.order',string="Sale Order", track_visibility='onchange', domain=[('sale_order_return','=',False)])
    sale_order_return_ids = fields.Many2many('sale.order', string="Sale Order", track_visibility='onchange', relation='sale_order_return_rel', column1='order_id', column2='sale_order_return_relation', domain=[('sale_order_return', '=', False)])
    sort_tracking_message = fields.Char('Sale order return change: ', track_visibility='onchange')
    invoice_return_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ], string='Invoice Status', compute='_get_invoice_return_status',readonly=True)
    check_show_button_return = fields.Boolean(compute="_check_show_button_return")

    def _check_show_button_return(self):
        for record in self:
            if (record.picking_ids.filtered(lambda p:p.state != 'cancel') and record.invoice_ids.filtered(lambda inv:inv.state != 'cancel')) or record.state == 'cancel':
                record.check_show_button_return = True
            else:
                record.check_show_button_return = False

    def _get_invoice_return_status(self):
        for record in self:
            if record.state not in ['sale','done']:
                record.invoice_return_status = 'no'
                record.invoice_status = 'no'
            elif not record.invoice_ids:
                record.invoice_return_status = 'to invoice'
                record.invoice_status = 'to invoice'
            else:
                record.invoice_return_status = 'invoiced'
                record.invoice_status = 'invoiced'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(sale_order_inherit, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and 'sale_order_return' in self._context:
            doc = etree.XML(result['arch'])
            if doc.xpath("//form/header/button"):
                nodes = doc.xpath("//form/header/button")
                for node in nodes:
                    if node.attrib.get('string') not in ['In','Hủy'] and node.attrib.get('name') != 'button_action_return_have_check' and node.attrib.get('name') != 'action_draft' \
                            and node.attrib.get('name') != 'print_excel' and node.attrib.get('name') != 'action_sale_cancel':
                        node.set('invisible', '1')
                        node.set('modifiers', """{"invisible": "true"}""")
            result['arch'] = etree.tostring(doc)
        if view_type in ['form','tree'] and 'sale_order_return' in self._context and result.get('toolbar', False) and 'action' in result['toolbar']:
            action_ids = result['toolbar'].get('action',False)
            action_remove_ids = []
            for action_id in action_ids:
                if action_id.get('xml_id') in ['tuanhuy_sale.action_multi_create_picking_record','sale.action_view_sale_advance_payment_inv','tuanhuy_sale.action_multi_create_account_invoice']:
                    action_remove_ids.append(action_id)
            for action_remove_id in action_remove_ids:
                result['toolbar'].get('action', False).remove(action_remove_id)
        if view_type == 'tree' and 'sale_order_return' in self._context:
            doc = etree.XML(result['arch'])
            nodes = doc.xpath("//field[@name='invoice_status']")
            for invoice_status in nodes:
                invoice_status.set('invisible', '1')
                invoice_status.set('modifiers', """{"tree_invisible": "true"}""")
            result['arch'] = etree.tostring(doc)
        else:
            doc = etree.XML(result['arch'])
            nodes = doc.xpath("//field[@name='invoice_return_status']")
            for invoice_return_status in nodes:
                invoice_return_status.set('invisible', '1')
                invoice_return_status.set('modifiers', """{"tree_invisible": "true"}""")
            result['arch'] = etree.tostring(doc)
        return result

    @api.model
    def default_get(self, fields):
        res = super(sale_order_inherit, self).default_get(fields)
        if 'sale_order_return' in self._context:
            res['sale_order_return'] = True
        return res

    @api.onchange('sale_order_return_id')
    def onchange_sale_order_return_id(self):
        if self.sale_order_return_id:
            self.partner_id = self.sale_order_return_id.partner_id

    @api.onchange('sale_order_return_ids')
    def onchange_sale_order_return_ids(self):
        self.sort_tracking_message = ', '.join(self.sale_order_return_ids.mapped('name'))
        if self.sale_order_return_ids:
            self.partner_id = self.sale_order_return_ids[0].partner_id

    @api.model
    def _fill_objects(self):
        products = self.search(['&', ('sale_order_return_id', '!=', False), ('sale_order_return_ids', '=', False)])
        for r in products:
            if not r.sale_order_return_ids and r.sale_order_return_id:
                r.sale_order_return_ids = [(4, r.sale_order_return_id.id)]
            else:
                r.sale_order_return_ids = False

    @api.multi
    def create_invoice_return(self):
        invoice_id = self.env['account.invoice'].create({
            'type' : 'out_refund',
            'origin': self.name,
            'partner_id' : self.partner_id.id,
            'date_invoice': self.date_order,
            # 'date_due': self.date_order,
            'date': self.date_order,
            'date_order' : self.date_order,
        })

        invoice_line = []
        account_id = self.env['account.account'].search([('code','=','5213')],limit=1).id or False
        for line in self.order_line:
            if line.product_id or line.quantity != 0:
                invoice_line.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'uom_id': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'price_discount' : line.price_discount,
                    'invoice_line_tax_ids': [(6,0,line.tax_id.ids)],
                    'name': line.product_id.display_name,
                    'account_id' : account_id,
                    'sale_line_ids' : [(6,0,line.ids)],
                    'date_invoice'  : self.date_order,
                }))
        invoice_id.get_taxes_values()
        invoice_id.with_context(journal_id=1).write({'invoice_line_ids': invoice_line})
        invoice_id.compute_taxes()
        invoice_id.action_invoice_open()
        return invoice_id

    @api.model
    def create(self, vals):
        result = super(sale_order_inherit, self).create(vals)
        if result.sale_order_return == True:
            result.name = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order.return') or _('New')
        return result

    def check_product_expired_time(self):
        product_check = False
        for line in self.order_line:
            date_now = datetime.strptime(self.date_order,DEFAULT_SERVER_DATETIME_FORMAT).date()
            product_group = line.product_id.group_id
            product_brand = line.product_id.brand_name_select
            product_group_id = False
            product_brand_id = False
            date_number = 0
            if product_group:
                product_group_id = self.env['product.to.date'].search([]).filtered(lambda ptd: product_group.id in ptd.product_group_id.ids)
            if product_brand:
                product_brand_id = self.env['product.to.date'].search([]).filtered(lambda ptd: product_brand.id in ptd.band_name_id.ids)
            if product_group_id and product_brand_id:
                product_to_date_id = product_group_id.filtered(lambda ptd: product_brand.id in ptd.band_name_id.ids)
                if product_to_date_id:
                    date_number = product_to_date_id[0].date_number
            if product_group_id and not product_brand_id:
                date_number = product_group_id[0].date_number
            if not product_group_id and product_brand_id:
                date_number = product_brand_id[0].date_number
            if not product_group_id and not product_brand_id:
                product_to_date_id = self.env['product.to.date'].search([('product_group_id','=', False),('band_name_id','=', False)])
                if product_to_date_id:
                    date_number = product_to_date_id[0].date_number
            if date_number:
                order_line = self.sale_order_return_ids.mapped('order_line').filtered(lambda l: l.product_id.id == self.product_id.id)
                if order_line and order_line[0].date_order:
                    date_order_to_now = datetime.strptime(order_line[0].date_order,DEFAULT_SERVER_DATETIME_FORMAT).date() + relativedelta(days=date_number)
                    if date_order_to_now < date_now:
                        product_check = True
                        break
        return product_check

    @api.multi
    def button_action_return_have_check(self):
        check = False
        if self.env['ir.values'].get_default('sale.config.settings', 'allow_check_expired_date') == 'allow':
            if not self.sale_order_return_ids or self.check_product_expired_time():
                check = True
            if check:
                return {
                    'name': 'Nhập mã pin',
                    'type': 'ir.actions.act_window',
                    'res_model': 'apply.by.pin.code',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': {'model': 'sale.order', 'record_id': self.id},
                    'target': 'new',
                }
            else:
                self.button_action_return()
        else:
            self.button_action_return()

    @api.multi
    def button_action_return(self):
        self.state = 'sale'
        self.confirmation_date = self.date_order

        for line in self.order_line:
            line.date_order = self.date_order
            if not line.order_id.procurement_group_id:
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)

        if not self.picking_ids.filtered(lambda p:p.state != 'cancel'):
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)

            location_id = False
            location_dest_id = False
            if picking_type_id:
                if picking_type_id.default_location_src_id:
                    location_id = picking_type_id.default_location_src_id.id
                elif self.partner_id:
                    location_id = self.partner_id.property_stock_customer.id
                else:
                    customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

                if picking_type_id.default_location_dest_id:
                    location_dest_id = picking_type_id.default_location_dest_id.id
                elif self.partner_id:
                    location_dest_id = self.partner_id.property_stock_customer.id
                else:
                    location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

            picking_id = self.env['stock.picking'].create({
                'picking_type_id': picking_type_id.id,
                'partner_id': self.partner_id.id,
                'origin': self.name,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'check_return_picking' : True,
                'min_date' : self.date_order,
            })

            picking_line = []
            for line in self.order_line:
                if line.product_id or line.quantity != 0:
                    price_unit = 0
                    if self.sale_order_return_ids and self.sale_order_return_ids.mapped('picking_ids'):
                        stock_move = self.sale_order_return_ids.mapped('picking_ids').mapped('move_lines').filtered(
                            lambda ml: ml.product_id == line.product_id)
                        stock_quants = stock_move.mapped('quant_ids')
                        amount = 0
                        qty = 0
                        for stock_quant in stock_quants:
                            amount += stock_quant.inventory_value
                            qty += qty
                        if amount == 0 or qty == 0:
                            price_unit = 0
                        else:
                            price_unit = amount / qty
                    price_unit = price_unit or line.product_id.standard_price
                    picking_line.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': location_id,
                        'location_dest_id': location_dest_id,
                        'name': line.product_id.display_name,
                        'group_id': self.procurement_group_id.id or False,
                        'procure_method': 'make_to_stock',
                        'warehouse_id': picking_type_id.warehouse_id.id,
                        'origin': self.name,
                        'price_unit' : price_unit,
                        'date': self.date_order,
                    }))

            picking_id.write({'move_lines': picking_line})
            picking_id.action_confirm()
            picking_id.force_assign()
            if self.sale_order_return_ids and all(sale_order.picking_ids for sale_order in self.sale_order_return_ids):
                picking_order_ids = self.sale_order_return_ids.mapped('picking_ids').filtered(lambda p: p.state != 'done')
                if not picking_order_ids:
                    picking_id.action_assign()
            if not self.sale_order_return_ids:
                picking_id.action_assign()

            #
            # if picking_id.state == 'assigned':
            #     picking_id.do_new_transfer()
                # stock_transfer_obj = self.env['stock.immediate.transfer']
                # stock_transfer_obj.create(stock_transfer_obj.with_context(
                #     {'active_id': picking_id.id}).default_get(stock_transfer_obj._fields)).process()

            picking_id.min_date = self.date_order

        if not self.invoice_ids.filtered(lambda inv:inv.state != 'cancel'):
            invoice_id = self.create_invoice_return()

            for line in self.order_line:
                invoice_lines = invoice_id.invoice_line_ids.filtered(lambda l: line.id in l.sale_line_ids.ids).ids or []
                line.invoice_lines = [(6,0,invoice_lines)]
            # invoice_id.action_invoice_open()

    @api.constrains('sale_order_return_ids', 'order_line')
    def constrains_sale_order_return_lines(self):
        if self.sale_order_return_ids:
            for product_id in self.order_line.mapped('product_id'):
                qties = self.order_line.filtered(lambda l: l.product_id.id == product_id.id).mapped('product_uom_qty')
                new_qty = sum(qties)
                qties = self.sale_order_return_ids.mapped('order_line').filtered(lambda l: l.product_id.id == product_id.id).mapped('product_uom_qty')
                old_qty = sum(qties)
                if new_qty > old_qty:
                    raise ValidationError(_("Số lượng sản phẩm %s không thể lớn hơn %s." % (product_id.name, old_qty)))

    def on_barcode_scanned(self, barcode):
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if not product:
            product_ids = self.env['product.barcode'].search([('name','=',barcode)]).product_id.ids
            product = self.env['product.template'].search([('id','in',product_ids)],limit=1).product_variant_id
        if product:
            corresponding_line = self.order_line.filtered(lambda r: r.product_id.barcode == barcode or barcode in r.product_id.barcode_ids.mapped('name'))
            if corresponding_line:
                corresponding_line[0].product_uom_qty += 1
                if self.sale_order_return:
                    corresponding_line[0].onchange_product_id_for_return(self.sale_order_return_ids.ids)
            else:
                line = self.order_line.new({
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': 1.0,
                    'price_unit': product.lst_price,
                })
                line.product_id_change()
                line.product_uom_change()
                line.onchange_product_for_ck(self.partner_id.id)
                if self.sale_order_return:
                    line.onchange_product_id_for_return(self.sale_order_return_ids.ids)
                if self.tax_id:
                    line.tax_id = [(6, 0, self.tax_id.ids)]
                    line.tax_sub= self.tax_id.amount
                self.order_line += line
            return
        else:
            raise ValidationError(_("Không tìm thấy sản phẩm với mã barcode này."))

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    sale_order_return = fields.Boolean(related="order_id.sale_order_return")

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if self.sale_order_return:
            return {}
        else:
            res = super(sale_order_line, self)._onchange_product_id_check_availability()
            return res

    @api.onchange('product_id')
    def onchange_product_id_for_return(self,sale_order=None):
        if ('sale_order_ctx' in self._context and self._context.get('sale_order_ctx')) or sale_order:
            if 'sale_order_ctx' in self._context:
                sale_id = self.env['sale.order'].browse(self._context.get('sale_order_ctx')[0][2])
            elif sale_order:
                sale_id = self.env['sale.order'].browse(sale_order)
            if not self.product_id:
                return {'domain': {
                    'product_id': [('id', 'in', sale_id.mapped('order_line').mapped('product_id').ids)]}}
            else:
                order_line = sale_id.mapped('order_line').filtered(lambda l: l.product_id.id == self.product_id.id)
                if order_line:
                    purchase_line = order_line[0]
                    self.product_uom_qty = sum(order_line.mapped('product_uom_qty'))
                    self.price_unit = purchase_line.price_unit
                    self.tax_sub = purchase_line.tax_sub
                    self.discount = purchase_line.discount
                    self.price_discount = purchase_line.price_discount