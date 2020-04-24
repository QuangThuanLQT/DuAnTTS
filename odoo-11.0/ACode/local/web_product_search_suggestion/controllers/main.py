# -*- coding: utf-8 -*-

import json
from difflib import SequenceMatcher

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.tts_modifier_website.controllers.website_sale_controllers import WebsiteSale


class WebsiteSaleSearch(WebsiteSale):

    @http.route(['/shop/get_suggest'], type='http', auth="public", methods=['GET'], website=True)
    def get_suggest_json(self, **kw):
        results = []
        query = kw.get('query')
        names = query.split(' ')
        domain = ['|' for k in range(len(names) - 1)] + [('key', 'ilike', name) for name in names]
        key_ids = request.env['product.search.keyword'].search(domain, limit=10, order='sequence').filtered(lambda key: key.type == 'key')
        key_ids = sorted(key_ids, key=lambda x: SequenceMatcher(None, query.lower(), x.key.lower()).ratio(),reverse=True)
        product_template_search = request.env['product.template'].search([('name', 'ilike', query)])
        product_template_search = sorted(product_template_search, key=lambda x: x.sequence_search)
        search_by_product = request.env['product.search.keyword'].search([('type', '=', 'product'), ('key', 'ilike', query)])
        list_product = []
        list_abc = []
        if key_ids:
            results = [{'value': 'Từ khóa hot', 'key': 'keyword'}]
            for key in key_ids:
                results.append({'value': key.key,
                                'key': 'keyword',
                                'data': {'id': key.id, 'after_selected': key.key},
                                })
                if query != '':
                    product_key = sorted(key.product_ids, key=lambda x: x.sequence_search)
                    for product in product_key:
                        if not product in list_abc:
                            list_product.append({
                                'value': product.name,
                                'key': 'product',
                                'data': {'id': product.id, 'after_selected': product.name},
                            })
                            list_abc.append(product)
        if query != '':
            for product_template in product_template_search:
                if product_template not in list_abc:
                    list_product.append({
                        'value': product_template.name,
                        'key': 'product',
                        'data': {'id': product_template.id, 'after_selected': product_template.name},
                    })
            for product_search in search_by_product:
                product_search_key = sorted(product_search.product_ids, key=lambda x: x.sequence_search)
                for product in product_search_key:
                    if product not in list_abc:
                        list_product.append({
                            'value': product.name,
                            'key': 'product',
                            'data': {'id': product.id, 'after_selected': product.name},
                        })
            for key_product in search_by_product:
                if key_product not in list_product:
                    list_product.append({
                        'value': key_product.key,
                        'key': 'key_product',
                        'data': {'id': key_product.id, 'after_selected': key_product.key},
                    })
        if list_product:
            for product in list_product:
                results.append(product)
        history_ids = request.env['product.search.history'].sudo().search([('user_id', '=', request.env.uid)], limit=10, order='date desc')
        # history_ids = sorted(history_ids, key=lambda x: SequenceMatcher(None, query.lower(), x.key.lower()).ratio(), reverse=True)
        history_ids = sorted(history_ids, key=lambda d: d.date, reverse=True)
        if history_ids:
            results.append({'value': 'Lịch sử tìm kiếm', 'key': 'history'})
            for product in history_ids:
                results.append({'value': product.key,
                                'key': 'history',
                                'data': {'id': product.id, 'after_selected': product.key},
                                })
        return json.dumps({
            'query': 'Unit',
            'suggestions': results
        })

    def _get_search_domain(self, search, category, attrib_values):
        domain = request.website.sale_product_domain()
        if search:
            key = request.env['product.search.keyword'].search([('key', '=', search)]).display_name
            key_ids = request.env['product.search.keyword'].search([('key', '=', search)]).mapped('product_ids')
            if key == search:
                domain += [('id', 'in', key_ids.ids)]
            else:
                for srch in search.split(" "):
                    keyword_ids = request.env['product.search.keyword'].sudo().search([('key', '=', srch)])
                    product_ids = keyword_ids.mapped('product_ids')
                    if product_ids:
                        domain += [
                            '|', '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                            ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch),
                            ('id', 'in', product_ids.ids)]
                    else:
                        domain += [
                            '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                            ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        return domain

    @http.route(['/shop/delete_history'], type='http', auth="public", methods=['GET'], website=True)
    def _delete_history_search(self, **kw):
        search_history = request.env['product.search.history'].search([('user_id', '=', request.env.uid)])
        search_history.unlink()
        return {}