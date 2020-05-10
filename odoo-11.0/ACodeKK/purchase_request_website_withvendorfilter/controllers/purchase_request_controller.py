from odoo import SUPERUSER_ID
from odoo import http
from odoo.http import request
import json
from odoo.http import Response
from odoo import models,fields,api,_
from odoo.addons.website.models.website import slug
from datetime import datetime
import datetime

import base64
from odoo.addons.web.controllers.main import serialize_exception,content_disposition


class WebsitePurchaseRequestForm(http.Controller):
    
    @http.route(['/request',
                 ], type='http', auth="public", website=True,csrf=False)
    def website_mydetail_controller_edit(self, **post):
        
        category_list = request.env['product.category'].sudo().search([])
        vendor_list = request.env['res.partner'].sudo().search([('supplier','=',True)])
        operation_list = request.env['stock.picking.type'].sudo().search([])
        product={}
        return request.render("purchase_request_website.form",{'product':product,'vendor_list':vendor_list,'category_list':category_list,'operation_list':operation_list})
    
    @http.route(['/request/detail',
                 ], type='http', auth="public", website=True,csrf=False)
    def website_mydetail(self, **post):
        category_id=request.params.get('category')
        vendor_id=request.params.get('vendor')
        partner=request.env['res.partner'].sudo().search([('id','=',request.params.get('vendor'))])
        product_category=request.env['product.category'].sudo().search([('id','=',request.params.get('category'))])
        operation_types=request.env['stock.picking.type'].sudo().search([('id','=',request.params.get('operation'))])
        values={}
        for product in request.env['product.product'].sudo().search([('categ_id','=',int(category_id)),('seller_ids.name','=',int(vendor_id))]):
            values.update({
                          product:product.name,
                          })
        return request.render("purchase_request_website.product_form",{'values':values,'partner':partner,'product_category':product_category,'operation_types':operation_types})

    
    @http.route(['/request/success',
                 ], type='http', auth="public", website=True,csrf=False)
    def website_mydetail_controller_save(self,redirect=None, **post):
        now=datetime.datetime.now()
        actual_time=now.strftime("%H:%M")
        minute=actual_time.split(":")[1]
        hour=actual_time.split(":")[0]
        b=float(minute)*(10/6)
        day=now.strftime("%A")
        ordering_time=request.env['ordering.time'].sudo().search([('day','=',day)])
        start_hour=str(ordering_time.start_time).split(".")[0]
        start_minute=str(ordering_time.start_time).split(".")[1]
        end_hour=str(ordering_time.end_time).split(".")[0]
        end_minute=str(ordering_time.end_time).split(".")[1]
        if float(hour) > float(start_hour) and float(hour) < float(end_hour):
            if post:
                self._process(post)
                return request.render("purchase_request_website.success",{})
        elif float(hour) == float(start_hour) and b >= float(start_minute) and float(hour) < float(end_hour):
            if post:
                self._process(post)
                return request.render("purchase_request_website.success",{})
        elif float(hour) > float(start_hour) and float(hour) == float(end_hour) and b <= float(end_minute):
            if post:
                self._process(post)
                return request.render("purchase_request_website.success",{})
        else:
            return request.render("purchase_request_website.fail",{})
        return
    
    def _process(self, post):
        picking_type=request.env['stock.picking.type'].sudo().search([('name','=',request.params.get('types'))]).id
        desc=request.env['product.product'].sudo().search([('id','=',post.get('product'))])
        purchase_id=request.env['purchase.request'].sudo().create({
                                                    'picking_type_id':picking_type,
                                                    'state':'to_approve',
                                                   })
        request.env['purchase.request.line'].sudo().create({
                                                            'product_id':post.get('product'),
                                                            'name':desc.name,
                                                            'product_qty':1.0,
                                                            'request_id':purchase_id.id,
                                                            })