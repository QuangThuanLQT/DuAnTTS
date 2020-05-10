# -*- coding: utf-8 -*-
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp

_STATES = [
    ('draft', 'Draft'),
    ('to_approve', 'To be approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected')
]

class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _company_get(self):
        return self.env.user.company_id.id

    @api.model
    def _get_default_requested_by(self):
        return self.env.user.id

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('purchase.request')

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'),('warehouse_id.company_id', '=', company_id)]).ids
        if not types:
            types = type_obj.search([('code', '=', 'incoming'),('warehouse_id', '=', False)]).ids
        return (types and types[0]) or False

    @api.multi
    @api.depends('name', 'origin', 'date_start', 'requested_by', 'assigned_to', 'description', 'company_id', 'line_ids', 'picking_type_id')
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ('to_approve', 'approved', 'rejected'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    _track = {
        'state': {
            'purchase_request.mt_request_to_approve':
                lambda self, cr, uid, obj,
                ctx=None: obj.state == 'to_approve',
            'purchase_request.mt_request_approved':
                lambda self, cr, uid, obj,
                ctx=None: obj.state == 'approved',
            'purchase_request.mt_request_rejected':
                lambda self, cr, uid, obj,
                ctx=None: obj.state == 'rejected',
        },
    }

    name = fields.Char('Request Reference', size=32, required=True, default=_get_default_name, track_visibility='onchange')
    origin = fields.Char('Source Document', size=32)
    date_start = fields.Date('Creation date', help="Date when the user initiated the request.", default=fields.Date.context_today, track_visibility='onchange')
    requested_by = fields.Many2one('res.users', 'Requested by', required=True, track_visibility='onchange', default=_get_default_requested_by)
    assigned_to = fields.Many2one('res.users', 'Approver', track_visibility='onchange')
    description = fields.Text('Description')
    company_id = fields.Many2one('res.company', 'Company', required=True, default=_company_get, track_visibility='onchange')
    line_ids = fields.One2many('purchase.request.line', 'request_id', 'Products to Purchase', readonly=False, copy=True, track_visibility='onchange')
    state = fields.Selection(selection=_STATES, string='Status', track_visibility='onchange', required=True, default='draft')
    is_editable = fields.Boolean(string="Is editable", compute="_compute_is_editable", readonly=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True, default=_default_picking_type)

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({'state': 'draft', 'name': self.env['ir.sequence'].next_by_code('purchase.request')})
        return super(PurchaseRequest, self).copy(default)

    @api.model
    def create(self, vals):
        mes_flwers_obj = False
        if vals.get('assigned_to'):
            assigned_to = self.env['res.users'].browse(vals.get('assigned_to'))
            mes_flwers_vals = {
                'res_model': self._name,
                'partner_id': assigned_to.partner_id.id,
            }
            mes_flwers_obj = self.env['mail.followers'].create(mes_flwers_vals)
            vals['message_follower_ids'] = [(4, mes_flwers_obj.id)]
        res = super(PurchaseRequest, self).create(vals)
        if mes_flwers_obj:
            mes_flwers_obj.res_id = res.id
        return res

    @api.multi
    def write(self, vals):
        self.ensure_one()
        if vals.get('assigned_to'):
            assigned_to = self.env['res.users'].browse(vals.get('assigned_to'))
            mes_flwers_vals = {
                'res_model': self._name,
                'res_id': self.id,
                'partner_id': assigned_to.partner_id.id,
            }
            vals['message_follower_ids'] = [(4, self.env['mail.followers'].create(mes_flwers_vals).id)]
        res = super(PurchaseRequest, self).write(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        return True

    @api.multi
    def button_to_approve(self):
        self.state = 'to_approve'
        return True

    @api.multi
    def button_approved(self):
        self.state = 'approved'
        return True

    @api.multi
    def button_rejected(self):
        self.state = 'rejected'
        return True

PurchaseRequest()
import time
class PurchaseRequestLineApproval(models.Model):
    _name = "purchase.request.line.approval"
    
    @api.model
    def get_prl(self):
        context = self.env.context
        if context.has_key('prl_id'):
            if context.get('prl_id', False):
                return self.env['purchase.request.line'].browse(context['prl_id'])
        return []
        
    name = fields.Char('Name', size=256, default=str(time.strftime("%Y-%m-%d %H:%M:%S")))
    purl = fields.Many2many('purchase.request.line', 'prl_approve_rel', 'prla_id', 'prl_id', 'POR', default=get_prl)
    
    @api.multi
    def approval(self):
        for record in self.browse(self.ids):
            for line in record.purl:
                self.env['purchase.request.line'].browse(line.id).write({'request_state':'approved'})
                request_id = self.env['purchase.request.line'].browse(line.id).request_id.id
                req_exist = self.env['purchase.request.line'].search([('request_id', '=', request_id),
                                 ('request_state', '=', 'to_approve')])
                if not req_exist:
                    self.env['purchase.request.line'].browse(line.id).request_id.button_approved()
        return 1
                

class PurchaseRequestLine(models.Model):
    _name = "purchase.request.line"
    _order = "id desc"
    _description = "Purchase Request Line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty', 'analytic_account_id', 'date_required', 'specifications')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ('to_approve', 'approved', 'rejected'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.multi
    def _compute_supplier_id(self):
        for rec in self:
            if rec.product_id:
                for product_supplier in rec.product_id.seller_ids:
                    rec.supplier_id = product_supplier.name.id

    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok', '=', True)], track_visibility='onchange')
    name = fields.Char('Description', size=256, track_visibility='onchange')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure', track_visibility='onchange')
    product_qty = fields.Float('Quantity', track_visibility='onchange', digits_compute=dp.get_precision('Product Unit of Measure'))
    request_id = fields.Many2one('purchase.request', 'Purchase Request', ondelete='cascade', readonly=True)
    company_id = fields.Many2one('res.company', related='request_id.company_id', string='Company', store=True, readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', track_visibility='onchange')
    requested_by = fields.Many2one('res.users', related='request_id.requested_by', string='Requested by', store=True, readonly=True)
    assigned_to = fields.Many2one('res.users', related='request_id.assigned_to', string='Assigned to', store=True, readonly=True)
    date_start = fields.Date(related='request_id.date_start', string='Request Date', readonly=True, store=True)
    description = fields.Text(related='request_id.description', string='Description', readonly=True, store=True)
    origin = fields.Char(related='request_id.origin', size=32, string='Source Document', readonly=True, store=True)
    date_required = fields.Date(string='Request Date', required=True, track_visibility='onchange', default=fields.Date.context_today)
    is_editable = fields.Boolean(string='Is editable', compute="_compute_is_editable", readonly=True)
    specifications = fields.Text(string='Specifications')
    request_state = fields.Selection(string='Request state', readonly=True, related='request_id.state', selection=_STATES, store=True)
    supplier_id = fields.Many2one('res.partner', string='Preferred supplier', compute="_compute_supplier_id")
    procurement_id = fields.Many2one('procurement.order', 'Procurement Order', readonly=True)

    @api.onchange('product_id', 'product_uom_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (name, self.product_id.code)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name
    
    @api.multi
    def button_approved(self):
        self.request_state = 'approved'
        request_id = self.request_id.id
        req_exist = self.env['purchase.request.line'].search([('request_id', '=', request_id),
                         ('request_state', '=', 'to_approve')])
        if not req_exist:
            self.request_id.button_approved()
        return True

PurchaseRequestLine()

class Company(models.Model):
    _inherit = 'res.company'
    
    po_double_validation = fields.Selection([
        ('one_step', 'Confirm purchase orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a purchase order'),
        ('three_step', 'Get 3 levels of approvals to confirm a purchase order')
        ], string="Levels of Approvals", default='one_step',
        help="Provide a double validation mechanism for purchases")
        
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order' 
    @api.multi
    def button_confirm(self):
        super(PurchaseOrder, self).button_confirm()
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or ((order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id))\
                    or (order.company_id.po_double_validation == 'two_step' and order.user_has_groups('purchase.group_purchase_manager'))) or (order.company_id.po_double_validation == 'three_step' and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id) or (order.company_id.po_double_validation == 'three_step' and order.user_has_groups('purchase_request.group_purchase_manager_threestep'))):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True