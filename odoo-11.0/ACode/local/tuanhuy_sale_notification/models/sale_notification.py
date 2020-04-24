# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class tuanhuy_sale_notification(models.Model):
    _name = 'sale.order.notification'




    def send_sale_notification(self):
        lines = []
        today = datetime.today()
        start_date = today.replace(hour=0, minute=0, second=0).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        end_date = today.replace(hour=23, minute=59, second=59).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        sale_order_ids = self.env['sale.order'].search([('date_order', '>=', start_date), ('date_order', '<=', end_date), ('state', '=', 'sale')])
        for order in sale_order_ids:
            partner_name = order.partner_id and order.partner_id.name
            for record in order.order_line:
                if record.product_id and record.product_id.product_tmpl_id:
                    group_sale_id = record.product_id.product_tmpl_id.group_sale_id
                    if group_sale_id:
                        discount = group_sale_id.group_line_ids.filtered(
                            lambda x: x.partner_id == partner_name or x.partner_name in partner_name)
                        if discount:
                            discount = discount[0].discount
                            if record.discount != discount:
                                data_order_line = {
                                    'order_name': record.order_id.name,
                                    'product_name': record.product_id.name,
                                    'price_unit': record.price_unit,
                                    'discount' : discount,
                                    'discount_sale': record.discount,
                                    'price_discount': ((100 - record.discount) * record.price_unit) / 100
                                }
                                lines.append(data_order_line)
                        else:
                            string = unicode("Ngoài những khách hàng đã lk", "utf-8")
                            discount = group_sale_id.group_line_ids.filtered(
                                lambda x: x.partner_name == string) and group_sale_id.group_line_ids.filtered(
                                lambda x: x.partner_name == string).discount or group_sale_id.group_line_ids[0].discount
                            if record.discount != discount:
                                if record.discount != discount:
                                    data_order_line = {
                                        'order_name': record.order_id.name,
                                        'product_name': record.product_id.name,
                                        'price_unit': record.price_unit,
                                        'discount': discount,
                                        'discount_sale': record.discount,
                                        'price_discount': ((100 - record.discount) * record.price_unit) / 100
                                    }
                                    lines.append(data_order_line)

        if lines:
            custom_body = """
                            <table style="border: 1px solid black;" width="100%">

                                <td widtd="20%">Đơn Hàng</td>

                                <td widtd="40%">Sản phẩm</td>

                                <td widtd="10%" style="text-align:center;">Đơn giá</td>

                                <td widtd="10%" style="text-align:center;">Chiết khấu</td>
                                
                                <td widtd="10%" style="text-align:center;">Chiết khấu khi bán</td>

                                <td widtd="10%" style="text-align:center;">Giá đã CK khi bán</td>

                        """
            for line in lines:
                custom_body += """
                                    <tr style="font-size:14px;border:1px solid black;">
                                        <td >%s</td>
                                        <td >%s</td>
                                        <td style="text-align:right;">%s</td>
                                        <td style="text-align:right;">%s</td>
                                        <td style="text-align:right;">%s</td>
                                        <td style="text-align:right;">%s</td>
                                    </tr>
                                    """ % ( line['order_name'],
                                        line['product_name'],
                                        '{:,}'.format(int(line['price_unit'])),
                                        line['discount'],
                                        line['discount_sale'],
                                        '{:,}'.format(int(line['price_discount'])),)
            custom_body += "</table>"

            body_html = custom_body
            user_email = self.env['res.users'].browse(1).email or self.env['res.users'].browse(1).partner_id.email
            company_email = self.env['res.users'].browse(1).company_id.email
            mail_values = {
                'email_from': company_email,
                'email_to': user_email,
                'subject': 'Sale Order Notification',
                'body_html': body_html,
            }
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()