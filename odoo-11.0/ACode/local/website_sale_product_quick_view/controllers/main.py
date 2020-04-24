# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.website_sale.controllers import main
from odoo.http import request

class WebsiteSaleExtend(main.WebsiteSale):

    @http.route(['/shop/product_quick_view'], type='json', auth="public", methods=['POST'], website=True)
    def product_quick_view(self, product_id, **kw):
        if product_id:
            return request.env['ir.ui.view'].render_template("website_sale_product_quick_view.product_extended_view", {
                'product': request.env['product.template'].browse(int(product_id)),
            })

    @http.route(['/shop/product_popup/update_option'], type='json', auth="public", methods=['POST'], website=True)
    def product_popup_options_update_json(self, data_list, lang=None, **kw):
        if lang:
            request.website = request.website.with_context(lang=lang)

        order = request.website.sale_get_order(force_create=1)

        product_list = []
        check_qty = False
        for data in data_list:
            quantity = int(data.get('quantity',0))
            product = data.get('product',False)
            if product:
                product_list.append({
                    'product': int(product),
                    'quantity': int(data.get('quantity',0))
                })
                product_id = request.env['product.product'].browse(int(data.get('product',False)))
                if int(data.get('quantity',False)) > product_id.sp_co_the_ban:
                    check_qty = True
                    return request.env['ir.ui.view'].render_template("tts_modifier_website.warning_error", {
                        'note': 'Bạn định mua %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                            quantity, product_id.display_name, product_id.sp_co_the_ban)
                    })

        if not check_qty:
            for product in product_list:
                if product.get('quantity'):
                    order._cart_update(
                        product_id=product.get('product'),
                        set_qty=product.get('quantity'),
                    )
                else:
                    order.with_context(product_zero=True)._cart_update(
                        product_id=product.get('product'),
                        set_qty=product.get('quantity'),
                    )

            return str(order.cart_quantity)

class WebsiteSale_showpop(http.Controller):

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
