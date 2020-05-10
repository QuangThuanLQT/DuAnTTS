# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
from xlrd import open_workbook
from datetime import datetime

class product_vendor_price(models.TransientModel):
    _name = 'product.vendor.price.file'

    seller_ids = fields.One2many('product.supplierinfo', 'product_price_id', 'Sản phẩm')

    import_data = fields.Binary(string="Tập tin")

    def import_csv(self):

        if 'active_id' in self._context:
            obj = self.env['product.vendor.price'].browse(self._context['active_id'])

            if self.import_data:

                data = base64.b64decode(self.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)
                row_error = []

                for row_no in range(sheet.nrows):
                    if row_no == 0 :
                        continue
                    row = (
                        map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                    print "Row: %s" %(row_no,)
                    product_model = self.env['product.template']
                    # vendor_model = self.env['res.partner']
                    # product_vendor_price_model = self.env['product.vendor.price']
                    uom_model = self.env['product.uom']
                    # supplierinfo_model = self.env['product.supplierinfo']

                    default_code = row[0]
                    name = row[2]
                    uom_name = row[3]
                    if not uom_name:
                        uom_name = 'Cái'
                    uom_id = uom_model.search([('name', '=', uom_name)], limit=1).id
                    if not uom_id:
                        print uom_name
                        uom_id = uom_model.search([('name', '=', 'Cái')], limit=1).id
                    brand = row[5]
                    source = row[6]
                    made_in = ''
                    listed_price = row[10] and float(row[10]) or 0
                    standard_price = row[9] and float(row[9]) or 0
                    barcode = row[1]
                    purchase_code = row[4]
                    product = product_model.search([('default_code','=', default_code)], limit=1)
                    if not product and default_code:
                        productinf = {
                            'name': name,
                            'barcode': barcode,
                            'default_code': default_code,
                            'uom_id': uom_id,
                            'uom_po_id': uom_id,
                            'list_price': listed_price,
                            'standard_price': standard_price,
                            'purchase_code': purchase_code,
                            'brand_name': brand,
                            'source': source,
                        }

                        if barcode:
                            product = product_model.search([('barcode', '=', barcode)], limit=1)
                            if product and product.id:
                                product.write(productinf)
                            else:
                                product = product_model.create(productinf)
                        else:
                            product = product_model.create(productinf)
                            product.fill_multi_barcode()
                    else:
                        productinf = {
                            'name': name,
                            # 'barcode': barcode,
                            # 'default_code': default_code,
                            'uom_id': uom_id,
                            'uom_po_id': uom_id,
                            'list_price': listed_price,
                            'standard_price': standard_price,
                            'purchase_code': purchase_code,
                            'brand_name': brand,
                            'source': source,
                        }

                        row_error.append({
                            'default_code': default_code,
                            'name': name,
                        })

                        product.write(productinf)
                if row_error:
                    return {
                        'name': 'Import Warning',
                        'type': 'ir.actions.act_window',
                        'res_model': 'import.warning',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'data_product': row_error,
                        }
                    }
                    # vendor_code = row[0]
                    # vendor_name = row[1]
                    # vendor_addr = row[2]
                    # vendorinf = {
                    #     'name': vendor_name,
                    #     'street': vendor_addr,
                    #     'street': vendor_addr,
                    # }
                    # vendor = vendor_model.search([('name', '=', vendor_name)],limit=1)
                    # if not vendor:
                    #     vendor = vendor_model.create(vendorinf)
                    # today = datetime.now().date()
                    #
                    # product_vendor_price = product_vendor_price_model.search([('partner_id', '=', vendor.id), ('date_from','<=',today), ('date_to','>=',today)])
                    # if not product_vendor_price:
                    #     product_vendor_price = product_vendor_price_model.create({
                    #         'partner_id':vendor.id
                    #     })
                    # seller = supplierinfo_model.search([('name', '=', vendor.id), ('product_tmpl_id','=', product.id)], limit=1)
                    # if not seller:
                    #     sellerinfor = {
                    #         'name':vendor.id,
                    #         'brand':brand,
                    #         'made_in':made_in,
                    #         'listed_price':listed_price,
                    #         'price': standard_price,
                    #         'product_tmpl_id': product.id,
                    #         'product_price_id': product_vendor_price.id
                    #     }
                    #     supplierinfo_model.create(sellerinfor)
                    # else:
                    #     sellerinfor = {
                    #         'brand':brand,
                    #         'made_in':made_in,
                    #         'listed_price':listed_price,
                    #         'price': standard_price,
                    #     }
                    #     seller.write(sellerinfor)