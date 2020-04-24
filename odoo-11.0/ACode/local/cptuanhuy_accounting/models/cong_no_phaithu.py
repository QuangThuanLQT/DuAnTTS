# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class CongNoPhaithu(models.Model):
    _inherit = 'cong.no.phaithu'

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'cong_no_phaithu')
        account_131 = self.env.ref('l10n_vn.chart131')
        query = """
                CREATE VIEW cong_no_phaithu AS (
                    SELECT
                        row_number() OVER () as id,
                        new.date as date,
                        new.confirm_date as confirm_date,
                        new.ref as ref,
                        new.description as description,
                        new.product_code as product_code,
                        new.product_qty as product_qty,
                        new.price_unit as price_unit,
                        new.account_id as account_id,
                        new.account_du_id as account_du_id,
                        new.partner_id as partner_id,
                        new.debit as debit,
                        new.credit as credit
                    FROM (
                    SELECT

                        aml.date as date,
                        aml.date as confirm_date,
                        am.ref as ref,
                        aml2.name as description,
                        p.default_code as product_code,
                        aml2.quantity as product_qty,
                        ABS(aml2.balance) / aml2.quantity as price_unit,
                        aml.account_id as account_id,
                        aml2.account_id as account_du_id,
                        aml.partner_id as partner_id,
                        aml2.credit as debit,
                        aml2.debit as credit
                    FROM
                        account_move_line aml
                    INNER JOIN
                        account_move am
                    ON
                        aml.move_id = am.id
                    INNER JOIN
                        account_move_line aml2
                    ON
                        aml2.move_id = am.id
                        AND aml2.id != aml.id
                    LEFT JOIN
                        product_product p
                    ON
                        aml2.product_id = p.id
                    WHERE
                        (am.ref LIKE '%s' OR am.ref LIKE '%s')
                        AND aml.account_id = %s
                    UNION ALL (
                        SELECT

                            aml.date as date,
                            aml.date as confirm_date,
                            am.ref as ref,
                            aml2.name as description,
                            p.default_code as product_code,
                            aml2.quantity as product_qty,
                            ABS(aml2.balance) as price_unit,
                            aml.account_id as account_id,
                            aml2.account_id as account_du_id,
                            aml.partner_id as partner_id,
                            CASE
                                WHEN aml2.credit > aml.debit THEN aml.debit
                                ELSE aml2.credit
                            END AS debit,
                            CASE
                                WHEN aml2.debit > aml.credit THEN aml.credit
                                ELSE aml2.debit
                            END AS credit
                        FROM
                            account_move_line aml
                        INNER JOIN
                            account_move am
                        ON
                            aml.move_id = am.id
                        INNER JOIN
                            account_move_line aml2
                        ON
                            aml2.move_id = am.id
                            AND aml2.account_id != %s
                        LEFT JOIN
                            product_product p
                        ON
                            aml2.product_id = p.id
                        WHERE
                            (am.ref IS NULL OR (am.ref NOT LIKE '%s' AND am.ref NOT LIKE '%s'))
                            AND ((aml.debit > 0 AND aml2.credit > 0) OR (aml.credit > 0 AND aml2.debit > 0))
                            AND aml.account_id = %s
                    )) as new
                )""" % ('SO%', 'RT0%', account_131.id, account_131.id, 'SO%', 'RT0%', account_131.id)
        self._cr.execute(query)