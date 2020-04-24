# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.http import request
from odoo.addons.website.models.website import slug


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def set_purchase_request_line(self, product_id=None, add_qty=None, set_qty=None):
        self.ensure_one()
        purchase_request = self.get_purchase_request()
        lines = purchase_request.get('line_ids', [])
        existlines = [line for line in lines if line.get('product_id')==product_id]
        try:
            index = existlines and existlines[0] in lines and lines.index(existlines[0])
        except Exception as e:
            index = -1

        quantity = 0
        if not existlines:
            index = -1
            product = request.env['product.product'].search([('id', '=', product_id)])
            attribute_values = []
            for attr_val in product.attribute_line_ids.sorted(key=lambda x: x.attribute_id.sequence):
                if len(attr_val.value_ids)==1:
                    attribute_values.append((attr_val.attribute_id.name, attr_val.value_ids[0].name))

            existlines = [{'product_id': product.id,
                'image': product.image_small,
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_tmpl_slug': slug(product.product_tmpl_id),
                'display_name': product.with_context(display_default_code=False).display_name,
                'description': product.description_purchase,
                'product_qty': 1,
                'attribute_values': attribute_values
                }]
            if add_qty:
                add_qty -= 1
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            quantity = existlines[0].get('product_qty') + (add_qty or 0)
        existlines[0]['product_qty'] = quantity
        if quantity <=0:
            lines.remove(existlines[0])
        else:
            if index<0:
                lines.append(existlines[0])
            else:
                lines[index] = existlines[0]
        purchase_request['line_ids'] = lines
        request.session['purchase_request'] = purchase_request
        return True

    @api.multi
    def _prepare_purchase_request_values(self, partner):
        self.ensure_one()
        default_user_id = partner.parent_id.user_id.id or partner.user_id.id
        values = {
            'requested_by': default_user_id,
            'partner_id': partner.id,
            'line_ids':[],
            'state': 'draft'
        }
        return values

    @api.multi
    def get_purchase_request(self, force_create=False):
        self.ensure_one()
        partner = self.env.user.partner_id
        purchase_request = request.session.get('purchase_request')
        
        # create pro if needed
        if not purchase_request:
            purchase_request = self._prepare_purchase_request_values(partner)
            request.session['purchase_request'] = purchase_request

        if purchase_request:
            # case when user emptied the cart

            # check for change of partner_id ie after signup
            if purchase_request.get('partner_id') != partner.id and request.website.partner_id.id != partner.id:
                # change the partner, and trigger the onchange
                purchase_request['partner_id'] = partner.id


        else:
            request.session['purchase_request'] = None
            return {}

        return purchase_request

