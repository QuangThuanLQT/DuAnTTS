# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from werkzeug.exceptions import Forbidden, NotFound
import odoo
from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import ValidationError
from odoo.addons.web.controllers.main import ensure_db, Session, Home
import logging

_logger = logging.getLogger(__name__)

class Home_inherit(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = request.env.ref('base.public_user').id

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if not uid:
                id = request.env['res.users'].sudo().search([('phone', '=', request.params['login'])])
                if id:
                    uid = request.session.authenticate(request.session.db, id.login,
                                                       request.params['password'])
            if uid is not False:
                request.params['login_success'] = True
                if not redirect:
                    redirect = '/web'
                    if request.uid:
                        user_id = request.env['res.users'].browse(request.uid)
                        if user_id.has_group('tts_modifier_access_right.group_khach_hang'):
                            redirect = '/shop'
                        employee_kd = request.env['hr.employee'].search(['|',('job_id.name', '=', 'Nhân viên kinh doanh'),('job_id.name', '=', 'Trưởng nhóm kinh doanh')])
                        if user_id in employee_kd.mapped('user_id'):
                            menu_id = request.env.ref('dashboard_sale_revenue.menu_sale_dashboard').id
                            action = request.env.ref('dashboard_sale_revenue.action_sale_dashboard').id
                            redirect = '/web#view_type=sale_dashboard_view&model=dashboard.sale.revenue&menu_id=%s&action=%s' % (menu_id,action)
                        employee_ceo = request.env['hr.employee'].search([('job_id.name', '=', 'CEO')])
                        if user_id in employee_ceo.mapped('user_id'):
                            menu_id = request.env.ref('tts_sale_report.menu_dashboard_widget_doanh_so').id
                            action = request.env.ref('tts_sale_report.dashboard_widget_doanh_so_action').id
                            redirect = '/web#view_type=form&model=board.board&menu_id=%s&action=%s' % (menu_id, action)
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = _("Wrong login/password")
        return request.render('web.login', values)

    @http.route('/', type='http', auth="public", website=True)
    def index(self, **kw):
        page = 'homepage'
        main_menu = request.website.menu_id or request.env.ref('website.main_menu', raise_if_not_found=False)
        if main_menu:
            if not request._context.get('uid', False):
                first_menu = request.env.ref('website.menu_homepage')
            else:
                first_menu = main_menu.child_id and main_menu.child_id[0]
            if first_menu:
                if first_menu.url and (
                not (first_menu.url.startswith(('/page/', '/?', '/#')) or (first_menu.url == '/'))):
                    return request.redirect(first_menu.url)
                if first_menu.url and first_menu.url.startswith('/page/'):
                    return request.env['ir.http'].reroute(first_menu.url)
        return self.page(page)
