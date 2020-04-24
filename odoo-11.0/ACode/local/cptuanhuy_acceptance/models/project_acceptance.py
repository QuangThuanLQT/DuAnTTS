# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class project_acceptance_line(models.Model):
    _name = 'project.acceptance.line'

    acceptance_id = fields.Many2one('project.acceptance')
    product_id = fields.Many2one('product.product', string='Sản phẩm')
    product_uom = fields.Many2one('product.uom', string='Đơn vị')
    product_qty = fields.Float(string='Số lượng')
    list_price = fields.Float(string='Giá bán', related='product_id.list_price')



class project_acceptance(models.Model):
    _name = 'project.acceptance'


    @api.model
    def _get_location(self):
        location = self.env.ref('cptuanhuy_stock.location_kct_stock')
        return location.id

    name            = fields.Char('Tên')
    sale_order_id   = fields.Many2one('sale.order','Đơn hàng',required=False)
    partner_id      = fields.Many2one('res.partner','Khách hàng')
    description     = fields.Text('Biên bản nghiệm thu')
    amount          = fields.Float('Giá trị nghiệm thu')
    date            = fields.Date('Ngày nghiệm thu')
    contract_id     = fields.Many2one('account.analytic.account','Hợp đồng', required=True)
    state           = fields.Selection([('draft', 'Bản thảo'),('cancel','Đã huỷ'),('done', 'Hoàn thành')], string='Trạng thái', default='draft', copy=False)
    invoice_ids     = fields.Many2many('account.invoice')
    invoice_count   = fields.Integer(compute="_compute_invoice", string='# of Bills', copy=False, default=0)
    location_id     = fields.Many2one('stock.location', 'Địa điểm', default=_get_location)
    picking_id      = fields.Many2one('stock.picking', string='Phiếu kho')
    line_ids        = fields.One2many('project.acceptance.line', 'acceptance_id', string='Chi tiết', state={'done':[('readonly',True)]})

    @api.depends('invoice_ids')
    def _compute_invoice(self):
        for order in self:
            order.invoice_count = len(self.invoice_ids.ids)

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def create_invoice(self):
        for record in self:
            if record.sale_order_id:
                payment_id = self.env['sale.advance.payment.inv'].create({
                    'advance_payment_method':'fixed',
                    'amount':record.amount,
                    'count':record.sale_order_id.id
                      # 'deposit_account_id'
                      # 'deposit_taxes_id'
                    })
                res = payment_id.with_context(active_ids=self.sale_order_id.ids,acceptance_id = self.id,open_invoices=True).create_invoices()

                # Create Picking
                picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
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
                        'location_id': self.location_id.id or location_id,
                        'location_dest_id': location_dest_id,
                        'min_date': datetime.today().date(),
                    })
                    picking_line = []
                    for line in self.line_ids:
                        if line.product_id or line.quantity != 0:

                            picking_line.append((0, 0, {
                                'product_id': line.product_id.id,
                                'product_uom_qty': line.product_qty,
                                'product_uom': line.product_uom.id,
                                'location_id': self.location_id.id or location_id,
                                'picking_type_id': picking_type_id.id,
                                'warehouse_id': picking_type_id.warehouse_id.id,
                                'location_dest_id': location_dest_id,
                                'name': line.product_id.display_name,
                                'procure_method': 'make_to_stock',
                                'origin': self.name,
                                'price_unit': line.list_price,
                                'date': datetime.today().date(),
                            }))

                    picking_id.write({'move_lines': picking_line})
                    record.write({'picking_id': picking_id.id})
                record.write({'state':'done'})
                return res

    @api.multi
    def action_cancel(self):
        for record in self:
            if record.invoice_ids:
                for invoice in record.invoice_ids:
                    invoice.action_invoice_cancel()
            record.write({'state': 'cancel'})

    @api.multi
    def set_to_draft(self):
        for record in self:
            record.write({'state': 'draft'})

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            if self.contract_id.partner_id:
                self.partner_id = self.contract_id.partner_id

    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        if self.sale_order_id:
            self.line_ids = None
            line_ids = self.line_ids.browse([])
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)

            for picking in self.sale_order_id.manual_picking_ids.filtered(lambda r: r.picking_type_id == picking_type and r.state == 'done'):
                for line in picking.move_lines:
                    line_data = {
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'list_price': line.product_id.list_price,
                        'product_qty': line.product_uom_qty,
                    }
                    line = self.line_ids.new(line_data)
                    line_ids += line
            for picking in self.sale_order_id.picking_ids.filtered(lambda r: r.picking_type_id == picking_type and r.state == 'done'):
                for line in picking.move_lines:
                    line_data = {
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'list_price': line.product_id.list_price,
                        'product_qty': line.product_uom_qty,
                    }
                    line = self.line_ids.new(line_data)
                    line_ids += line
            self.line_ids = line_ids



class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    acceptance_ids = fields.One2many('project.acceptance','contract_id',string='Quản lý nghiệm thu')

class sale_order(models.Model):
    _inherit = 'sale.order'

    acceptance_ids = fields.One2many('project.acceptance','sale_order_id', string='Quản lý nghiệm thu')

