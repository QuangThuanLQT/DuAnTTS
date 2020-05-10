# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
from odoo import api, fields, models, _

import odoo.addons.decimal_precision as dp
import logging
from odoo.tools.float_utils import float_round
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	def _compute_quantities_dict(self):
		# TDE FIXME: why not using directly the function fields ?
		
		variants_available = self.mapped('product_variant_ids')._product_available()
		prod_available = {}
		for template in self:
			qty_available = 0
			virtual_available = 0
			incoming_qty = 0
			outgoing_qty = 0
			for p in template.product_variant_ids:
				qty_available += variants_available[p.id]["qty_available"]
				virtual_available += variants_available[p.id]["virtual_available"]
				incoming_qty += variants_available[p.id]["incoming_qty"]
				outgoing_qty += variants_available[p.id]["outgoing_qty"]
				################################### CODE ADDED BY JAHANGIR ####################################
				if template.is_pack and template.wk_product_pack:
					ACT_VARIANTS = template.mapped('product_variant_ids')
					for pp in template.wk_product_pack:
						template.product_variant_ids += pp.product_name
					variants_available.update(template.mapped('product_variant_ids')._product_available())
					qty_avail = []
					vir_avail = []
					inco_qty = []
					outgo_qty = []
					for pp in template.wk_product_pack:
						qty_avail.append(variants_available[pp.product_name.id]["qty_available"]/pp.product_quantity)
						vir_avail.append(variants_available[pp.product_name.id]["virtual_available"]/pp.product_quantity)
						inco_qty.append(variants_available[pp.product_name.id]["incoming_qty"]/pp.product_quantity)
						outgo_qty.append(variants_available[pp.product_name.id]["outgoing_qty"]/pp.product_quantity)
					qty_available = min(qty_avail)
					virtual_available = min(vir_avail)
					incoming_qty = min(inco_qty)
					outgoing_qty = min(outgo_qty)
					template.product_variant_ids = ACT_VARIANTS
			################################### CODE CLOSED BY JAHANGIR ####################################
			prod_available[template.id] = {
				"qty_available": qty_available,
				"virtual_available": virtual_available,
				"incoming_qty": incoming_qty,
				"outgoing_qty": outgoing_qty,
			}

		return prod_available

