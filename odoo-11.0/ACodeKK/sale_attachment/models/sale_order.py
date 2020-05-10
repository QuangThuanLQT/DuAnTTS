# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class sale_order(models.Model):
    _inherit = 'sale.order'

    attachment_ids = fields.One2many('sale.attachment.line', 'order_id', string="Attachment Lines")

    @api.multi
    def action_confirm(self):
        res = super(sale_order, self).action_confirm()
        for record in self:
            pickings = record.mapped('picking_ids')
            for picking in pickings:
                for attachment in record.attachment_ids:
                    attachment.picking_id = picking.id
            return res


class sale_attachment(models.Model):
    _name = 'sale.attachment'

    name = fields.Char('Name')
    # attachment_ids = fields.One2many('sale.attachment.line', 'attachment_id', string="Attachment Lines")


class sale_attachment_line(models.Model):
    _name = 'sale.attachment.line'

    order_id = fields.Many2one('sale.order', string="Sale Order")
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    picking_id = fields.Many2one('stock.picking', string="Stock Picking")
    attachment_id = fields.Many2one('sale.attachment', string="Attachment")
    stock_checklist = fields.Boolean(string="Stock Checklist", default=False)


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    attachment_ids = fields.One2many('sale.attachment.line', 'picking_id', string="Attachment Lines")
    reason = fields.Text()

    @api.multi
    def do_new_transfer(self):
        res = super(stock_picking, self).do_new_transfer()
        for record in self:
            for attachment in record.attachment_ids:
                if not attachment.stock_checklist:
                    if not 'skip_stock_checklist_check' in self._context:
                        return {
                            'name': _('Warning'),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'stock.picking.wizard',
                            'view_id': self.env.ref('sale_attachment.stock_picking_wizard_view').id,
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                        }
        return res


class Wizard(models.TransientModel):
    _name = 'stock.picking.wizard'

    name = fields.Char(string="Reason")
    description = fields.Char(default="Missing attachment. Do you want continue?", readonly=True)

    def confirm(self):
        stock_picking = self.env['stock.picking'].browse(self._context['active_id'])
        stock_picking.reason = self.name
        return stock_picking.with_context(skip_stock_checklist_check=True).do_new_transfer()