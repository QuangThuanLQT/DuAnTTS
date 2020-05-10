# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from werkzeug.exceptions import Forbidden, NotFound

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import ValidationError
import odoo.addons.web.controllers.main as web_main

import logging

_logger = logging.getLogger(__name__)

class Viewmodifier(web_main.View):
    @http.route('/web/view/edit_custom', type='json', auth="user")
    def edit_custom(self, custom_id=False, arch=False):
        """
        Edit a custom view

        :param int custom_id: the id of the edited custom view
        :param str arch: the edited arch of the custom view
        :returns: dict with acknowledged operation (result set to True)
        """

        custom_view = request.env['ir.ui.view.custom'].browse(custom_id)
        custom_view.write({'arch': arch})
        return {'result': True}

class TtsModifierWebsite(http.Controller):

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        order = request.website.sale_get_order(force_create=1)
        qty_this_product_in_order = sum(order.order_line.filtered(lambda l: l.product_id.id == product_id).mapped('product_uom_qty'))
        product = request.env['product.product'].browse(product_id)
        quantity = set_qty
        if quantity > 0 and quantity > product.sp_co_the_ban + qty_this_product_in_order:
            value = {}
            order = request.website.sale_get_order()
            value['cart_quantity'] = order.cart_quantity
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            value['website_sale.cart_lines'] = request.env['ir.ui.view'].render_template("website_sale.cart_lines", {
                'website_sale_order': order,
                'compute_currency': lambda price: from_currency.compute(price, to_currency),
                'suggested_products': order._cart_accessories()
            })
            value['warning'] = 'Bạn định mua %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                    quantity, product.display_name, product.sp_co_the_ban + qty_this_product_in_order)
            return value
        else:
            if order.state != 'draft':
                request.website.sale_reset()
                return {}
            value = order._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty)
            if not order.cart_quantity:
                request.website.sale_reset()
                order.unlink()
                return {}
            if not display:
                return None

            order = request.website.sale_get_order()
            value['cart_quantity'] = order.cart_quantity
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            value['website_sale.cart_lines'] = request.env['ir.ui.view'].render_template("website_sale.cart_lines", {
                'website_sale_order': order,
                'compute_currency': lambda price: from_currency.compute(price, to_currency),
                'suggested_products': order._cart_accessories()
            })
            return value

class WebsiteAccount(http.Controller):
    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "ward", "district_id", "city_id", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name"]

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def details(self, redirect=None, **post):
        partner = request.env.user.partner_id
        values = {
            'error': {},
            'error_message': []
        }

        if post:
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                values.update({'zip': values.pop('zipcode', '')})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        city = request.env['feosco.city'].sudo().search([])
        district_list = request.env['feosco.district'].sudo().search([])
        ward_list = request.env['feosco.ward'].sudo().search([])
        values.update({
            'partner': partner,
            'countries': countries,
            'city': city,
            'district': district_list,
            'wards': ward_list,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
        })

        return request.render("website_portal.details", values)

    def details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        # vat validation
        if data.get("vat") and hasattr(request.env["res.partner"], "check_vat"):
            if data.get("country_id"):
                data["vat"] = request.env["res.partner"].fix_eu_vat_number(int(data.get("country_id")), data.get("vat"))
            if request.website.company_id.sudo().vat_check_vies:
                # force full VIES online check
                check_func = request.env["res.partner"].vies_vat_check
            else:
                # quick and partial off-line checksum validation
                check_func = request.env["res.partner"].simple_vat_check
            vat_country, vat_number = request.env["res.partner"]._split_vat(data.get("vat"))
            if not check_func(vat_country, vat_number):  # simple_vat_check
                error["vat"] = 'error'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data.iterkeys() if k not in self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message

class WebsiteSaleOptions(WebsiteSale):

    @http.route(['/shop/modal'], type='json', auth="public", methods=['POST'], website=True)
    def modal(self, product_id, **kw):
        pricelist = request.website.get_current_pricelist()
        product_context = dict(request.context)
        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
        # fetch quantity from custom context
        product_context.update(kw.get('kwargs', {}).get('context', {}))

        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: request.env['res.currency']._compute(from_currency, to_currency, price)

        main_product_attr_ids = []
        product_list =  []
        for product in product_id:
            product_id = request.env['product.product'].with_context(product_context).browse(int(product[1]))
            quantity = int(product[0])
            if product_id and quantity:
                if quantity > product_id.sp_co_the_ban:
                    return request.env['ir.ui.view'].render_template("tts_modifier_website.warning_error", {
                        'note': 'Bạn định mua %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                            quantity, product_id.display_name, product_id.sp_co_the_ban)
                    })
                product_list.append({
                    'product' : product_id,
                    'quantity' : quantity,
                })
                # for variant in self.get_attribute_value_ids(product_id):
                #     if variant[0] == product_id.id:
                #         # We indeed need a list of lists (even with only 1 element)
                #         main_product_attr_ids.append(variant)
                #         break



        return request.env['ir.ui.view'].render_template("website_sale_options.modal", {
            'product_list': product_list,
            'compute_currency': compute_currency,
            'get_attribute_value_ids': self.get_attribute_value_ids,
            'main_product_attr_ids': main_product_attr_ids,
        })

    @http.route(['/shop/cart/update_option'], type='http', auth="public", methods=['POST'], website=True,
                multilang=False)
    def cart_options_update_json(self, product_id, add_qty=1, set_qty=0, goto_shop=None, lang=None, **kw):
        if lang:
            request.website = request.website.with_context(lang=lang)

        order = request.website.sale_get_order(force_create=1)
        product = request.env['product.product'].browse(int(product_id))

        option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
        optional_product_ids = []
        product_list = []
        check_qty = False
        for k, v in kw.items():
            if 'product_id_' in k:
                product_list.append({
                    'product' : int(k.split('product_id_')[1]),
                    'quantity' : int(v)
                })
                product_id = request.env['product.product'].browse(int(k.split('product_id_')[1]))
                if int(v) > product_id.sp_co_the_ban:
                    check_qty = True
        #     elif "attribute-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
        #         optional_product_ids.append(int(v))
        #
        attributes = self._filter_attributes(**kw)
        #
        # quantity = int(add_qty) or int(set_qty) or 0

        if check_qty:
            return str('warning_error')
        else:

        # value = {}
        # if add_qty or set_qty:
        #     value = order._cart_update(
        #         product_id=int(product_id),
        #         add_qty=add_qty,
        #         set_qty=set_qty,
        #         attributes=attributes,
        #         optional_product_ids=optional_product_ids
        #     )

        # options have all time the same quantity
        # for option_id in optional_product_ids:
        #     order._cart_update(
        #         product_id=option_id,
        #         set_qty=value.get('quantity'),
        #         attributes=attributes,
        #         linked_line_id=value.get('line_id')
        #     )
            product_list = self.add_product_zero(product_list)
            for product in product_list:
                if product.get('quantity') == 0:
                    order.with_context(product_zero=True)._cart_update(
                        product_id=product.get('product'),
                        set_qty=product.get('quantity'),
                        # attributes=attributes,
                    )
                else:
                    order._cart_update(
                        product_id=product.get('product'),
                        set_qty=product.get('quantity'),
                        # attributes=attributes,
                    )

            return str(order.cart_quantity)

    def add_product_zero(self, product_list):
        list_product = [value.get('product') for value in product_list]
        product_ids = request.env['product.product'].browse(list_product)
        if product_ids:
            product_tmpl_id = product_ids.mapped('product_tmpl_id')
            attribute_value_ids = product_ids.mapped('attribute_value_ids')
            attribute_ids = attribute_value_ids.mapped('attribute_id')
            if attribute_ids and len(attribute_ids) > 1:
                attribute_value_id = attribute_value_ids[0] if attribute_value_ids else False
                if attribute_value_id:
                    product_add = request.env['product.product'].search([('product_tmpl_id', '=', product_tmpl_id.id), (
                    'attribute_value_ids', '=', attribute_value_id.id), ('id', 'not in', list_product)])
                    for product in product_add:
                        product_list.append({
                            'product': product.id,
                            'quantity': 0
                        })
        return product_list

    def get_attribute_value_ids(self, product):
        """ list of selectable attributes of a product

        :return: list of product variant description
           (variant id, [visible attribute ids], variant price, variant sale price)
        """
        # product attributes with at least two choices
        quantity = product._context.get('quantity') or 1
        product = product.with_context(quantity=quantity)

        visible_attrs_ids = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id').ids
        to_currency = request.website.get_current_pricelist().currency_id
        attribute_value_ids = []
        for variant in product.product_variant_ids:
            if to_currency != product.currency_id:
                price = variant.currency_id.compute(variant.website_public_price, to_currency) / quantity
            else:
                price = variant.website_public_price / quantity
            visible_attribute_ids = [v.id for v in variant.attribute_value_ids if v.attribute_id.id in visible_attrs_ids]
            availability = 1
            if variant.availability == 'in_stock':
                availability = 2
            elif variant.availability == 'warning':
                availability = 3
            attribute_value_ids.append([variant.id, visible_attribute_ids, variant.website_price, price, variant.sp_co_the_ban,availability,variant.availability_number])
        return attribute_value_ids
