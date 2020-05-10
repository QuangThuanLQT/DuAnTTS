# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import Warning
from odoo.tools.translate import _

class ProductPackWizard(models.TransientModel):
	_name = 'product.pack.wizard' 	

	product_name = fields.Many2one('product.product',string='PACK',required=True)
	quantity = fields.Integer('Quantity',required=True ,default=1)
	

	@api.multi
	def add_product_button(self):
		taxes_id = []
		if self.product_name.taxes_id:
			taxes_id = self.product_name.taxes_id.ids
		product_obj = self.product_name.wk_product_pack
		self.env['sale.order.line'].create({'order_id':self._context['active_id'],'product_id':self.product_name.id, 'name':self.product_name.name,'price_unit':self.product_name.list_price,'product_uom':1,'product_uom_qty':self.quantity,'tax_id':[(6, 0, taxes_id)]})	
		return True

	@api.onchange('quantity', 'product_name')
	def onchange_quantity_pack(self):
		if self.quantity:
			if self.product_name:
				for prod in self.product_name.wk_product_pack:
					if self.quantity > prod.product_name.virtual_available:
						warn_msg = _('You plan to sell %s but you have only  %s quantities of the product %s available, and the total quantity to sell is  %s !!'%(self.quantity, prod.product_name.virtual_available, prod.product_name.name, self.quantity * prod.product_quantity)) 
						return {
					    'warning': {
					        'title': 'Invalid value',
					        'message': warn_msg
					    }
					}



 