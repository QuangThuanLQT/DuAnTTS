# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
from openerp import api, fields, models, _
from openerp import tools
import logging
from openerp.exceptions import ValidationError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	is_pack = fields.Boolean(string = 'Is product pack')
	wk_product_pack = fields.One2many(comodel_name = 'product.pack', inverse_name = 'wk_product_template',string = 'Product pack')
	pack_stock_management = fields.Selection([('decrmnt_pack','Decrement Pack Only'),('decrmnt_products','Decrement Products Only'),('decrmnt_both','Decrement Both')],'Pack Stock Management', default='decrmnt_products')

	@api.onchange('pack_stock_management')
	def select_type_default_pack_mgmnt_onchange(self):
		pk_dec = self.pack_stock_management
		if pk_dec == 'decrmnt_products':
			prd_type = 'service'
		elif pk_dec == 'decrmnt_both':
			prd_type = 'product'
		else:
			prd_type = 'consu'
		self.type = prd_type

	@api.model
	def create(self, vals):
		if vals.get('is_pack'):
			if not vals.get('wk_product_pack'):
				raise ValidationError('No products in this pack. Select atleast one product.')
		return super(ProductTemplate, self).create(vals)
	
	@api.onchange('type')
	def select_default_pack_mgmnt_onchange_type(self):
		if self.is_pack:
			prd_type = self.type
			if prd_type == 'service':
				pack_type = 'decrmnt_products'
			elif prd_type == 'product':
				pack_type = 'decrmnt_both'
			else:
				pack_type = 'decrmnt_pack'
			self.pack_stock_management = pack_type

class ProductProduct(models.Model):
	_inherit = "product.product"


	@api.onchange('pack_stock_management')
	def select_type_default_pack_mgmnt_onchange(self):
		pk_dec = self.pack_stock_management
		if pk_dec == 'decrmnt_products':
			prd_type = 'service'
		elif pk_dec == 'decrmnt_both':
			prd_type = 'product'
		else:
			prd_type = 'consu'
		self.type = prd_type
		

class ProductPack(models.Model):
	_name = 'product.pack'

	product_name = fields.Many2one(comodel_name='product.product', string ='Product', required=True)
	product_quantity = fields.Integer(string='Quantity', required = True, default = 1)
	wk_product_template = fields.Many2one(comodel_name='product.template', string='Product pack')
	wk_image = fields.Binary(related ='product_name.image_medium',string='Image', store=True)
	price = fields.Float(related ='product_name.lst_price',string='Product Price')
	uom_id = fields.Many2one(related ='product_name.uom_id' ,string="Unit of Measure", readonly="1")
	name = fields.Char(related = 'product_name.name',readonly="1")

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	@api.multi
	def _action_procurement_create(self):
		"""
		Create procurements based on quantity ordered. If the quantity is increased, new
		procurements are created. If the quantity is decreased, no automated action is taken.
		"""
		res = super(SaleOrderLine, self)._action_procurement_create()
		new_procs = self.env['procurement.order'] #Empty recordset
		for line in self:
			if line.product_id.is_pack:
				if not line.order_id.procurement_group_id and line.product_id.pack_stock_management == 'decrmnt_products':
					vals = line.order_id._prepare_procurement_group()
					line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)
				vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)
				temp = vals
				if line.product_id.pack_stock_management != 'decrmnt_pack':
					for pack_obj in line.product_id.wk_product_pack:			
						temp['product_id'] = pack_obj.product_name.id
						temp['product_qty'] = line.product_uom_qty * pack_obj.product_quantity
						temp['product_uom'] = pack_obj.product_name.uom_id.id
						temp['message_follower_ids'] = False
						temp['sale_line_id'] = False
						new_proc = self.env["procurement.order"].create(temp)
						new_procs += new_proc
		new_procs.run()
		return res
		
	@api.onchange('product_id', 'product_uom_qty')
	def _onchange_product_id_check_availability(self):
		res = super(SaleOrderLine, self)._onchange_product_id_check_availability()
		product_obj = self.product_id
		if product_obj.type == 'product':
			if product_obj.is_pack:
				warning_mess = {}
				for pack_product in product_obj.wk_product_pack:
					qty = self.product_uom_qty
					_logger.info("#################%r",qty)
					if qty * pack_product.product_quantity > pack_product.product_name.virtual_available:
						warning_mess = {
                    			'title': _('Not enough inventory!'),
                    			'message' : ('You plan to sell %s but you have only  %s quantities of the product %s available, and the total quantity to sell is  %s !!'%(qty, pack_product.product_name.virtual_available, pack_product.product_name.name,qty * pack_product.product_quantity))
                				}
						return {'warning': warning_mess}
			return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
