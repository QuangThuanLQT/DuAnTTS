# -*- coding: utf-8 -*-
from odoo import http

# class JobCostingManagementExtension(http.Controller):
#     @http.route('/job_costing_management_extension/job_costing_management_extension/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/job_costing_management_extension/job_costing_management_extension/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('job_costing_management_extension.listing', {
#             'root': '/job_costing_management_extension/job_costing_management_extension',
#             'objects': http.request.env['job_costing_management_extension.job_costing_management_extension'].search([]),
#         })

#     @http.route('/job_costing_management_extension/job_costing_management_extension/objects/<model("job_costing_management_extension.job_costing_management_extension"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('job_costing_management_extension.object', {
#             'object': obj
#         })