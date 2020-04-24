# -*- coding: utf-8 -*-

import re
from odoo import models, api

class MassReconcileSimple(models.AbstractModel):
    _name = 'mass.reconcile.simple'
    _inherit = 'mass.reconcile.base'

    # has to be subclassed
    # field name used as key for matching the move lines
    _key_field = None

    def get_ref_account_move(self,move_id):
        self.env.cr.execute("SELECT ref FROM account_move WHERE id = '%s'"%(move_id))
        aml_ref = self.env.cr.fetchall()
        if aml_ref:
            aml_ref = aml_ref[0][0]
            return aml_ref
        return False

    @api.multi
    def rec_auto_lines_simple(self, lines):
        if self._key_field is None:
            raise ValueError("_key_field has to be defined")
        count = 0
        res = []

        if self._name == 'mass.reconcile.simple.partner.ref':
            while (count < len(lines)):
                list_reconciled = []
                sum_amount_line_count = lines[count]['debit'] + lines[count]['credit']
                sum_amount_line_i = 0.0
                for i in xrange(0, len(lines)):
                    try:
                        if lines[count][self._key_field] != lines[i][self._key_field]:
                            continue
                    except Exception, e:
                        continue

                    if i == count:
                        continue

                    line_name = lines[count]['name']
                    if 'VAT' in line_name:
                        break

                    check_same_ref = False
                    order_names = re.findall(r'[SOPRT]+\d{1,4}/\d{4}', line_name)
                    if not order_names:
                        break
                    for name in order_names:
                        try:
                            if 'S' in name and '/' in name:
                                if 'SO' in name:
                                    name_order = "SO%s/%s" % (
                                    '{0:06}'.format(int(name.split('SO')[1].split('/')[0])), name.split('/')[1])
                                else:
                                    name_order = "SO%s/%s" % (
                                        '{0:06}'.format(int(name.split('S')[1].split('/')[0])), name.split('/')[1])
                                if name_order == self.get_ref_account_move(lines[i]['move_id']):
                                    check_same_ref = True
                            elif 'P' in name and '/' in name:
                                name_order = "PO%s/%s" % (
                                '{0:06}'.format(int(name.split('P')[1].split('/')[0])), name.split('/')[1])
                                if name_order == self.get_ref_account_move(lines[i]['move_id']):
                                    check_same_ref = True
                            elif 'RT' in name and '/' in name:
                                name_order = "RT%s/%s" % (
                                '{0:06}'.format(int(name.split('RT')[1].split('/')[0])), name.split('/')[1])
                                if name_order == self.get_ref_account_move(lines[i]['move_id']):
                                    check_same_ref = True
                            elif 'RTP' in name and '/' in name:
                                name_order = "RTP%s/%s" % (
                                '{0:06}'.format(int(name.split('RTP')[1].split('/')[0])), name.split('/')[1])
                                if name_order == self.get_ref_account_move(lines[i]['move_id']):
                                    check_same_ref = True
                        except Exception, e:
                            pass
                    if not check_same_ref:
                        continue

                    check = False
                    if lines[count]['credit'] > 0 and lines[i]['debit'] > 0:
                        credit_line = lines[count]
                        debit_line = lines[i]
                        check = True
                    elif lines[i]['credit'] > 0 and lines[count]['debit'] > 0:
                        credit_line = lines[i]
                        debit_line = lines[count]
                        check = True
                    if not check:
                        continue
                    sum_amount_line_i += lines[i]['debit'] + lines[i]['credit']
                    list_reconciled.append((credit_line,debit_line,i,count))
                if list_reconciled and 1000 >= abs(round(sum_amount_line_count - sum_amount_line_i,2)):
                    for l_reconciled in list_reconciled:
                        credit_line = l_reconciled[0]
                        debit_line = l_reconciled[1]
                        if not credit_line.get('reconciled', False) and not debit_line.get('reconciled', False):
                            reconciled, dummy = self._reconcile_lines(
                                [credit_line, debit_line],
                                allow_partial=False
                            )
                        else:
                            reconciled = False

                        if reconciled:
                            res += [credit_line['id'], debit_line['id']]
                            del lines[l_reconciled[2]]
                            if l_reconciled[2] < l_reconciled[3]:
                                count -= 1

                count += 1
                print count
            return res

        else:

            while (count < len(lines)):
                for i in xrange(count + 1, len(lines)):
                    try:
                        if lines[count][self._key_field] != lines[i][self._key_field]:
                            break
                    except Exception, e:
                        continue

                    check = False
                    if lines[count]['credit'] > 0 and lines[i]['debit'] > 0:
                        credit_line = lines[count]
                        debit_line = lines[i]
                        check = True
                    elif lines[i]['credit'] > 0 and lines[count]['debit'] > 0:
                        credit_line = lines[i]
                        debit_line = lines[count]
                        check = True
                    if not check:
                        continue
                    if not credit_line.get('reconciled', False) and not debit_line.get('reconciled', False):
                        reconciled, dummy = self._reconcile_lines(
                            [credit_line, debit_line],
                            allow_partial=False
                        )
                    else:
                        reconciled = False

                    if reconciled:
                        res += [credit_line['id'], debit_line['id']]
                        del lines[i]
                        if self._name != 'mass.reconcile.simple.partner.ref':
                            # del lines[i]
                            break
                count += 1
                print count
            return res

    @api.multi
    def _simple_order(self, *args, **kwargs):
        return "ORDER BY account_move_line.%s" % self._key_field

    @api.multi
    def _action_rec(self):
        """Match only 2 move lines, do not allow partial reconcile"""
        select = self._select()
        select += ", account_move_line.%s " % self._key_field
        where, params = self._where()
        where += " AND account_move_line.%s IS NOT NULL " % self._key_field

        where2, params2 = self._get_filter()
        query = ' '.join((
            select,
            self._from(),
            where, where2,
            self._simple_order()))

        self.env.cr.execute(query, params + params2)
        lines = self.env.cr.dictfetchall()
        return self.rec_auto_lines_simple(lines)


class MassReconcileSimpleName(models.TransientModel):
    _name = 'mass.reconcile.simple.name'
    _inherit = 'mass.reconcile.simple'

    # has to be subclassed
    # field name used as key for matching the move lines
    _key_field = 'name'


class MassReconcileSimplePartner(models.TransientModel):
    _name = 'mass.reconcile.simple.partner'
    _inherit = 'mass.reconcile.simple'

    # has to be subclassed
    # field name used as key for matching the move lines
    _key_field = 'partner_id'

class MassReconcileSimplePartnerRef(models.TransientModel):
    _name = 'mass.reconcile.simple.partner.ref'
    _inherit = 'mass.reconcile.simple'

    # has to be subclassed
    # field name used as key for matching the move lines
    _key_field = 'partner_id'


class MassReconcileSimpleReference(models.TransientModel):
    _name = 'mass.reconcile.simple.reference'
    _inherit = 'mass.reconcile.simple'

    # has to be subclassed
    # field name used as key for matching the move lines
    _key_field = 'ref'
