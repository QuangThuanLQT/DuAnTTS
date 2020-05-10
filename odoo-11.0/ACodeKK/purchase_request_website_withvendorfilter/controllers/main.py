# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from datetime import date
from datetime import datetime
import datetime


PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class TableCompute(object):

    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= PPR:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(PPR):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products, ppg=PPG):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        for p in products:
            x = min(max(1, 1), PPR)
            y = min(max(1, 1), PPR)
            if index >= ppg:
                x = y = 1

            pos = minpos
            while not self._check_place(pos % PPR, pos / PPR, x, y):
                pos += 1
            # if 21st products (index 20) and the last line is full (PPR products in it), break
            # (pos + 1.0) / PPR is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= ppg and ((pos + 1.0) / PPR) > maxy:
                break

            if x == 1 and y == 1:   # simple heuristic for CPU optimization
                minpos = pos / PPR

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos / PPR) + y2][(pos % PPR) + x2] = False
            self.table[pos / PPR][pos % PPR] = {
                'product': p, 'x': x, 'y': y,
                'class': " ".join(map(lambda x: x.html_class or '', '')) # p.website_style_ids
            }
            if index <= ppg:
                maxy = max(maxy, y + (pos / PPR))
            index += 1

        # Format table according to HTML needs
        rows = self.table.items()
        rows.sort()
        rows = map(lambda x: x[1], rows)
        for col in range(len(rows)):
            cols = rows[col].items()
            cols.sort()
            x += len(cols)
            rows[col] = [c for c in map(lambda x: x[1], cols) if c]

        return rows


class WebsitePurchase(http.Controller):

    def get_attribute_value_ids(self, product):
        """ list of selectable attributes of a product

        :return: list of product variant description
           (variant id, [visible attribute ids])
        """
        # product attributes with at least two choices
        quantity = product._context.get('quantity') or 1
        product = product.with_context(quantity=quantity)

        visible_attrs_ids = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id').ids
        attribute_value_ids = []
        for variant in product.product_variant_ids:
            visible_attribute_ids = [v.id for v in variant.attribute_value_ids if v.attribute_id.id in visible_attrs_ids]
            attribute_value_ids.append([variant.id, visible_attribute_ids])
        return attribute_value_ids

    def _get_search_order(self, post):
        return '%s , id desc' % post.get('order', 'name asc')

    def _get_search_domain(self, search, attrib_values):
        domain = [('purchase_ok', '=', True)]
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                    ('description_purchase', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

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

    @http.route([
        '/purchase',
        '/purchase/page/<int:page>',
    ], type='http', auth='public', website=True)
    def purchase(self, page=0, search='', ppg=False, **post):
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attributes_ids = set([v[0] for v in attrib_values])
        attrib_set = set([v[1] for v in attrib_values])

        domain = []
        if request.params.get('category'):
            category_id=request.params.get('category')
            all_categ = request.env.ref('purchase_request_website.all_categ').id
            print("===all_categ==",all_categ)
            if all_categ == int(category_id):
                domain = []
            else:
                domain = [('categ_id','=',int(category_id))]
        print("============111=======",request.params.get('category'),domain)
        if request.params.get('vendor'):
            
            vendor_id=request.params.get('vendor')
            all_vendor = request.env.ref('purchase_request_website.all_vendor').id
            if all_vendor == int(vendor_id) and domain == []:
                domain = []
            elif all_vendor == int(vendor_id) and domain != []:
                domain = domain
            else:
                domain += [('seller_ids.name','=',int(vendor_id))]

            
        print("============222=======",request.params.get('vendor'),domain) 
        if domain == []:
            domain = self._get_search_domain(search, attrib_values)
        else:
            domain += [('purchase_ok', '=', True)]
        
        print("============333=======",domain)

        keep = QueryURL('/purchase', search=search, attrib=attrib_list, order=post.get('order'))
        request.context = dict(request.context, partner=request.env.user.partner_id)

        url = "/purchase"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template']

        product_count = Product.sudo().search_count(domain)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = Product.sudo().search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            selected_products = Product.sudo().search(domain, limit=False)
            attributes = ProductAttribute.sudo().search([('attribute_line_ids.product_tmpl_id', 'in', selected_products.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)
        vendor_list = request.env['res.partner'].sudo().search([('supplier','=',True)])
        category_list = request.env['product.category'].sudo().search([])
        values = {
            'vendor_list':vendor_list,
            'category_list':category_list,
            'search': search,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'attributes': attributes,
            'keep': keep,
        }
        if request.params.get('vendor'):
            vendor = request.env['res.partner'].sudo().browse(int(request.params.get('vendor')))
            values['selected_vendor'] = vendor.name
        if request.params.get('category'):
            category = request.env['product.category'].sudo().browse(int(request.params.get('category')))
            values['selected_category'] = category.name
        return request.render("purchase_request_website.products", values)


    @http.route(['/purchase/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, search='', **kwargs):
        product_context = dict(request.env.context,
                               active_id=product.id,
                               partner=request.env.user.partner_id)

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        keep = QueryURL('/purchase', search=search, attrib=attrib_list)

        values = {
            'search': search,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'keep': keep,
            'main_object': product,
            'product': product,
            'get_attribute_value_ids': self.get_attribute_value_ids,
        }
        return request.render("purchase_request_website.product", values)

    @http.route(['/purchase/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        purchase_request = request.website.get_purchase_request()

        values = {
            'purchase_request': purchase_request,
        }
        if post.get('type') == 'popover':
            # force no-cache so IE11 doesn't cache this XHR
            return request.render("purchase_request_website.cart_popover", values, headers={'Cache-Control': 'no-cache'})

        return request.render("purchase_request_website.cart", values)

    @http.route(['/purchase/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        request.website.get_purchase_request(force_create=1)
        request.website.set_purchase_request_line(
            product_id=int(product_id),
            add_qty=float(add_qty),
            set_qty=float(set_qty),
        )
        return request.redirect("/purchase/cart")

    @http.route(['/purchase/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, add_qty=None, set_qty=None, display=True):
        # order = request.website.get_purchase_request(force_create=1)      
        request.website.set_purchase_request_line(product_id=product_id, add_qty=add_qty, set_qty=set_qty)
        purchase_request = request.website.get_purchase_request()
        value = {'cart_quantity': len(purchase_request.get('line_ids', []))}
        value['purchase_request_website.cart_lines'] = request.env['ir.ui.view'].render_template("purchase_request_website.cart_lines", {
            'purchase_request': purchase_request,
        })
        return value

    def _process_pr(self, post,purchase_request):
        lines_data = purchase_request.get('line_ids')
        line_obj = request.env['purchase.request.line']
        request_lines = []
        for line_data in lines_data:
            line = line_obj.create({'product_id':line_data.get('product_id'),
                'date_required': date.today()
                })
            line.onchange_product_id()
            line.write({'product_qty': line_data.get('product_qty')})
            request_lines.append(line.id)


        purchase_request.update(request.env['purchase.request'].default_get(['name', 'requested_by', 'company_id', 'picking_type_id']))
        purchase_request['line_ids'] = [(6, 0, request_lines)]
        purchase_request = request.env['purchase.request'].create(purchase_request)
        task_list_data = {
            'user_id': request.env.user.id,
            'res_model_id': request.env['ir.model'].search([('model', '=', 'purchase.request')]).id,
            'res_id': purchase_request.id,
            'date_deadline': str(date.today()),
        }

        #request.env['mail.activity'].create(task_list_data)
        purchase_request.button_to_approve()
        del request.session['purchase_request']
        return purchase_request
        
    @http.route(['/purchase/confirm'], type='http', auth="public", website=True,csrf=False)
    def confirm_order(self, **post):
        if request.env.user == request.env.ref('base.public_user'):
            return request.redirect('/web/login?redirect=/purchase/cart')
        purchase_request = request.website.get_purchase_request()


        now=datetime.datetime.now()
        actual_time=now.strftime("%H:%M")
        minute=actual_time.split(":")[1]
        hour=actual_time.split(":")[0]
        hour = int(hour)+8
       
        b=float(minute)*(10/6)
        day=now.strftime("%A")
        ordering_time=request.env['ordering.time'].sudo().search([('day','=',day)])
        start_hour=str(ordering_time.start_time).split(".")[0]
        start_minute=str(ordering_time.start_time).split(".")[1]
        end_hour=str(ordering_time.end_time).split(".")[0]
        end_minute=str(ordering_time.end_time).split(".")[1]
        if float(hour) > float(start_hour) and float(hour) < float(end_hour):
            
            purchase_request = self._process_pr(post,purchase_request)
            return request.render("purchase_request_website.pr_created", {'purchase_request': purchase_request})
        elif float(hour) == float(start_hour) and b >= float(start_minute) and float(hour) < float(end_hour):
            purchase_request = self._process_pr(post,purchase_request)
            return request.render("purchase_request_website.pr_created", {'purchase_request': purchase_request})
        elif float(hour) > float(start_hour) and float(hour) == float(end_hour) and b <= float(end_minute):
            purchase_request = self._process_pr(post,purchase_request)
            return request.render("purchase_request_website.pr_created", {'purchase_request': purchase_request})
        else:
            return request.render("purchase_request_website.fail",{})
        
        return 
        
         
