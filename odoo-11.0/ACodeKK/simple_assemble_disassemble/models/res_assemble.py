# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResAssemble(models.Model):
    _name = 'res.assemble'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _description = 'Product Assemble'

    material_id           = fields.One2many('assemble.materials', 'assemble_id', 'Materials', readonly=True, states={'draft': [('readonly', False)]})
    name                  = fields.Char(string='Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', True)]}, index=True, default='New')
    product_id            = fields.Many2one('product.template', 'Product',readonly=True, states={'draft': [('readonly', False)]})
    product_product_id    = fields.Many2one('product.product', compute='_compute_product_id', string='Product (2)')
    quantity_pro          = fields.Integer('Quantity', readonly=True, states={'draft': [('readonly', False)]},default=1)
    date_assemble         = fields.Date('Date', readonly=True, states={'draft': [('readonly', False)]}, default=fields.Date.context_today)
    stock_production_prod = fields.Many2one('stock.production.lot', 'Serial Number', readonly=True, states={'draft': [('readonly', False)]})
    location_src_id       = fields.Many2one('stock.location', 'Location', readonly=True, states={'draft': [('readonly', False)]})
    move_id               = fields.Many2one('stock.move', 'Move')
    quant_available       = fields.Float('Quantity Available', compute='_compute_quant_available')
    state                 = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel','Cancelled')
    ], string='Status', default='draft')

    @api.multi
    def _compute_quant_available(self):
        for record in self:
            quant_available = 0
            if record.move_id and record.move_id.id:
                if record.location_src_id and record.location_src_id.id:
                    for quant in record.move_id.quant_ids:
                        if quant.location_id and quant.location_id.id == record.location_src_id.id:
                            quant_available += quant.qty
            record.quant_available = quant_available

    @api.depends('product_id')
    def _compute_product_id(self):
        for record in self:
            product = self.env['product.product'].search([
                ('product_tmpl_id','=',record.product_id.id)
            ], limit=1)
            record.product_product_id = product.id

    @api.onchange('product_id', 'quantity_pro')
    def onchange_product_id(self):
        if self.product_id:
            data = []
            for line in self.product_id.material_ids:
                data.append((0, 0, {'product_id': line.product_id.id, 'qty_pro': line.material_quantity * self.quantity_pro}))
            self.material_id = data

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('res.assemble') or 'New'
        result = super(ResAssemble, self).create(vals)
        return result

    @api.multi
    def action_assemble(self):
        move_obj = self.env['stock.move']

        if not self.material_id:
            raise UserError('Can not assemble without materials')

        for line in self.material_id:
            if line.qty_pro > line.product_id.qty_available:
                raise UserError('%s : Quantity greater than the on hand quantity (%s)' % (line.product_id.name, line.product_id.qty_available))

        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1).id
        if not picking_type_id:
            raise ValidationError(_('Please Setup for Internal Transfer location'))

        for record in self:
            credit_moves = move_obj.browse([])

            # Calculating the product_data from the materials
            product_data = {}
            for line in self.material_id:
                if line.product_id.id not in product_data:
                    product_data.update({line.product_id.id: line.qty_pro})
                else:
                    product_data.update({line.product_id.id: line.qty_pro + product_data.get(line.product_id.id)})

            # Step1: Checking material
            total_price = 0
            for line in record.material_id:
                line_product     = line.product_id
                line_product_qty = line.qty_pro
                if line_product.type == 'product':
                    available_qty = line_product.with_context(location=record.location_src_id.id)._product_available().get(line_product.id, {}).get('qty_available')
                    if available_qty < line_product_qty:
                        raise ValidationError(_('Material ' + line_product.name + ' have not enough stock.'))

                    move_data = {
                        'product_id'       : line_product.id,
                        'product_uom'      : line_product.uom_id.id,
                        'name'             : 'Deducted %s' % (line.product_id.name,),
                        'location_id'      : record.location_src_id.id,
                        'location_dest_id' : line_product.property_stock_production.id,
                        'product_uom_qty'  : line_product_qty,
                        'picking_type_id'  : picking_type_id,
                        # 'restrict_lot_id'  : record.stock_production_prod.id or False,
                    }
                    move_id = move_obj.create(move_data)
                    move_id.action_confirm()
                    move_id.action_assign()
                    move_id.with_context(from_assemble=True).action_done()
                    line.move_id = move_id

                    credit_moves += move_id
                    for quant in move_id.quant_ids:
                        total_price += quant.inventory_value

            assemple_product = record.product_product_id
            if assemple_product.type == 'product':
                # increasing qty of main product
                move_data = {
                    'product_id'      : assemple_product.id,
                    'product_uom_qty' : record.quantity_pro,
                    'product_uom'     : assemple_product.uom_id.id,
                    'name'            : 'Produced %s' % (assemple_product.name),
                    'date_expected'   : fields.Datetime.now(),
                    'procure_method'  : 'make_to_stock',
                    'location_id'     : assemple_product.property_stock_production.id,
                    'location_dest_id': record.location_src_id.id,
                    'origin'          : record.name,
                    'restrict_lot_id' : record.stock_production_prod.id or False,
                    'price_unit'      : total_price / record.quantity_pro,
                }
                move_id = self.env['stock.move'].create(move_data)
                move_id.action_assign()
                move_id.with_context(from_assemble=True).action_done()
                record.move_id = move_id

                record.create_journal_entry(credit_moves)

        self.write({'state': 'done'})
        return True

    @api.multi
    def create_journal_entry(self, credit_moves):
        self.ensure_one()

        account_move_lines = []
        credit_total = 0

        # TODO: Calculation credit move data
        for move in credit_moves:
            credit_value = 0
            for quant in move.quant_ids:
                credit_value += quant.inventory_value
            credit_total += credit_value

            credit_data = {
                'name'           : move.product_id.name,
                'product_id'     : move.product_id.id,
                'quantity'       : move.product_uom_qty,
                'product_uom_id' : move.product_id.uom_id.id,
                'ref'            : 'Deducted %s' % (move.product_id.name,),
                'credit'         : credit_value if credit_value > 0 else 0,
                'debit'          : 0,
                'account_id'     : move.product_id.categ_id.property_stock_valuation_account_id.id,
            }
            account_move_lines.append((0, 0, credit_data))

        # TODO: Calculation debit move data
        debit_data = {
            'name'           : self.product_product_id.name,
            'product_id'     : self.product_product_id.id,
            'quantity'       : self.quantity_pro,
            'product_uom_id' : self.product_product_id.uom_id.id,
            'ref'            : 'Assemble %s' % (self.product_product_id.name,),
            'credit'         : 0,
            'debit'          : credit_total if credit_total > 0 else 0,
            'account_id'     : self.product_product_id.categ_id.property_stock_valuation_account_id.id,
        }
        account_move_lines.append((0, 0, debit_data))

        move = self.env['account.move'].create({
            'name'       : '/',
            'journal_id' : self.product_id.categ_id.property_stock_journal.id,
            'date'       : fields.Date.today(),
            'line_ids'   : account_move_lines,
            # 'asset_id'   : self.id,
            'ref'        : self.name,
        })
        move.post()

        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

ResAssemble()

class AssembleMaterials(models.Model):
    _name = 'assemble.materials'

    assemble_id = fields.Many2one('res.assemble', 'Materials')
    product_id  = fields.Many2one('product.product', 'Product')
    qty_pro     = fields.Integer('Quantity')
    stock_lot   = fields.Many2one('stock.production.lot', 'Serial Number')
    move_id     = fields.Many2one('stock.move', 'Stock Move')

AssembleMaterials()

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def assemble_form_view(self):
        ctx = dict()
        form_id = self.env['ir.model.data'].sudo().get_object_reference('simple_assemble_disassemble', 'res_assemble_form_view')[1]
        ctx.update({
            'default_product_id': self.id,
        })
        action = {
            'type'      : 'ir.actions.act_window',
            'view_type' : 'form',
            'view_mode' : 'form',
            'res_model' : 'res.assemble',
            'views'     : [(form_id, 'form')],
            'view_id'   : form_id,
            'target'    : 'new',
            'context'   : ctx,
        }
        return action

ProductTemplate()
