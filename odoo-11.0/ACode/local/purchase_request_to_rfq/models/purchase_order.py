# -*- coding: utf-8 -*-
from openerp import _, api, exceptions, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_rl_ids = fields.One2many('po.request.line','po_id',string="Purchase Request Line")

    @api.model
    def _purchase_request_confirm_message_content(self, po, request, request_dict):
        if not request_dict:
            request_dict = {}
        title = _('Order confirmation %s for your Request %s') % (
            po.name, request.name)
        message = '<h3>%s</h3><ul>' % title
        message += _('The following requested items from Purchase Request %s '
                     'have now been confirmed in Purchase Order %s:') % (
            request.name, po.name)

        for line in request_dict.values():
            message += _('<li><b>%s</b>: Ordered quantity %s %s, Planned date %s</li>') % (line['name'],
                 line['product_qty'],
                 line['product_uom'],
                 line['date_planned'],)
        message += '</ul>'
        return message

    @api.multi
    def _purchase_request_confirm_message(self):
        request_obj = self.env['purchase.request']
        for po in self:
            requests_dict = {}
            for line in po.order_line:
                for request_line in line.purchase_request_lines:
                    request_id = request_line.request_id.id
                    if request_id not in requests_dict:
                        requests_dict[request_id] = {}
                    date_planned = "%s" % line.date_planned
                    data = {
                        'name': request_line.name,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.name,
                        'date_planned': date_planned,
                    }
                    requests_dict[request_id][request_line.id] = data
            for request_id in requests_dict:
                request = request_obj.browse(request_id)
                message = self._purchase_request_confirm_message_content(
                    po, request, requests_dict[request_id])
                request.message_post(body=message, subtype='mail.mt_comment')
        return True

    @api.multi
    def _purchase_request_line_check(self):
        for po in self:
            for line in po.order_line:
                for request_line in line.purchase_request_lines:
                    if request_line.purchase_state == 'done':
                        raise exceptions.Warning(
                            _('Purchase Request %s has already '
                              'been completed') % request_line.request_id.name)
        return True

    @api.multi
    def wkf_confirm_order(self):
        self._purchase_request_line_check()
        res = super(PurchaseOrder, self).wkf_confirm_order()
        self._purchase_request_confirm_message()
        return res


    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self.purchase_rl_ids.purchase_state = 'purchase'
        for prl_rec in self.purchase_rl_ids or []:
            if self.state == 'purchase':
                prl_rec.prl_id.purchase_state = 'purchase'
        return res

    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                print "**************",picking
                print "sssssssssssssssssss",self
                picking.po_request_id = self.id or False
                moves = order.order_line._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel')).action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
                moves.force_assign()
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)

        return True

PurchaseOrder()


class PORequestLine(models.Model):
    _name ='po.request.line'

    po_id = fields.Many2one('purchase.order',string="PO")
    prl_id = fields.Many2one('purchase.request.line',string="PRL ID")
    product_id = fields.Many2one('product.product',string="Product")

PORequestLine()

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    def _compute_has_purchase_request_lines(self):
        for rec in self:
            rec.has_purchase_request_lines = bool(rec.purchase_request_lines)

    purchase_request_lines = fields.Many2many(
        'purchase.request.line',
        'purchase_request_purchase_order_line_rel',
        'purchase_order_line_id',
        'purchase_request_line_id',
        'Purchase Request Lines', readonly=True, copy=False)

    has_purchase_request_lines = fields.Boolean(
        compute="_compute_has_purchase_request_lines",
        string="Has Purchase Request Lines")

    prl_id = fields.Many2one('purchase.request.line', string="Request Line")


    @api.multi
    def action_openRequestLineTreeView(self):
        """
        :return dict: dictionary value for created view
        """
        request_line_ids = []
        for line in self:
            request_line_ids = [request_line.id for request_line in line.purchase_request_lines]
        domain = [('id', 'in', request_line_ids)]
        return {'name': _('Purchase Request Lines'),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.request.line',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': domain}

PurchaseOrderLine()