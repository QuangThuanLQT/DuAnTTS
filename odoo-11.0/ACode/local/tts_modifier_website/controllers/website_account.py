# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from werkzeug.exceptions import Forbidden, NotFound

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website_portal_sale.controllers.main import website_account
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)



class website_account(website_account):


    @http.route(['/my/quotes', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotes(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        # domain = [
        #     ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        #     ('state', 'in', ['sent', 'cancel'])
        # ]

        domain = [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sent', 'cancel'])
        ]

        archive_groups = self._get_archive_groups('sale.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = SaleOrder.sudo().search_count(domain)
        # make pager
        pager = request.website.pager(
            url="/my/quotes",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'quotations': quotations,
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/quotes',
        })
        return request.render("website_portal_sale.portal_my_quotations", values)

    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        # domain = [
        #     ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        #     ('state', 'in', ['sale', 'done'])
        # ]
        domain = [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sale', 'done'])
        ]
        archive_groups = self._get_archive_groups('sale.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = SaleOrder.sudo().search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = SaleOrder.sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'order',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/orders',
        })
        return request.render("website_portal_sale.portal_my_orders", values)