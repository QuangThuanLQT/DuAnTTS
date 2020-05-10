# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import common

class TestProject(common.TransactionCase):
    def test_create_data(self):
        # Create a new project with the test
        test_product = self.env['product.product'].create({
            'name': 'TestProject'
        })

        self.assertEqual(test_product.name, 'TestProject')

        self.assertEqual(test_product.sp_ban_chua_giao, 0)
        self.assertEqual(test_product.sp_da_bao_gia, 0)
        self.assertEqual(test_product.sp_co_the_ban, 0)