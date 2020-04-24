# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from datetime import timedelta
import xmlrpclib
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
#!/usr/bin/env python
# coding: utf-8

class gia_von_popup(models.Model):
    _name = 'gia.von.popup'

    start_date  = fields.Datetime('Từ ngày',required=True)
    doing_date  = fields.Datetime('Thời gian thực hiện', required=True)
    complete_date    = fields.Datetime('Thời gian hoàn thành')
    end_date    = fields.Datetime('Tới ngày')
    state       = fields.Selection([('draft','Bản nháp'),('schedule','Lên kế hoạch'),('in_progress','Đang chạy'),('done','Hoàn thành')],string='Trạng thái',default='draft')
    note        = fields.Text("Ghi chú")


    @api.multi
    def compute_gia_von(self):
        self.write({'state':'schedule'})
        gia_von_id = self.env['gia.von.popup'].search([('state','=','schedule')],limit=1,order='doing_date asc')
        if gia_von_id:
            self.env.ref('tuanhuy_gia_von.cron_tinh_gia_von').sudo().write({'active':True,'nextcall': self.doing_date,'args':str(tuple(gia_von_id.ids))})

    def add_note(self,note):
        self.note = note
        self.env.cr.commit()

    @api.multi
    def schedule_tinh_gia_von(self,args):
        if args:
            gia_von_id = self.browse(args)
            self.env.cr.execute("UPDATE gia_von_popup SET state = 'in_progress' where id = %s"%args)
            self.env.cr.commit()
            print "\nSTART time:", datetime.datetime.today()

            start_date = gia_von_id.start_date
            end_date = gia_von_id.end_date or False

            # TODO: Optimize the performance by using sql query
            # Step-1: Disable cron picking
            query = "UPDATE ir_cron SET active=false WHERE name = '%s'" % ('Cron Create Picking From Sale',)
            self.env.cr.execute(query)

            query = "UPDATE ir_cron SET active=false WHERE name = '%s'" % ('Update Picking To Confirm',)
            self.env.cr.execute(query)
            
            query = "UPDATE ir_cron SET active=false WHERE name = '%s'" % ('Save Picking History',)
            self.env.cr.execute(query)
            
            # Step0: Get old data
            print "Step0: Prepare data"
            po_picking_dones = []
            query = "SELECT origin FROM stock_picking WHERE state='%s' AND min_date >= '%s' AND origin LIKE '%s' ORDER BY min_date asc" % ('done', start_date, 'PO%')
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    po_picking_dones.append(query_line[0])
            print "po_picking_dones = %s - %s" % (po_picking_dones, len(po_picking_dones))
            note = ''
            note = "po_picking_dones : " + ' ,'.join(line for line in po_picking_dones) + '\n'
            gia_von_id.add_note(note)


            po_picking_assigned = []
            query = "SELECT origin FROM stock_picking WHERE state IN ('assigned', 'partially_available') AND min_date >= '%s' AND origin LIKE '%s' ORDER BY min_date asc" % (start_date, 'PO%')
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    po_picking_assigned.append(query_line[0])
            print "po_picking_assigned = %s - %s" % (po_picking_assigned, len(po_picking_assigned))
            note += "po_picking_assigned : " + ' ,'.join(line for line in po_picking_assigned) + '\n'
            gia_von_id.add_note(note)

            return_has_so = []
            query = "SELECT DISTINCT so.name, so.date_order FROM sale_order_return_rel sr INNER JOIN sale_order so ON so.id = sr.order_id WHERE so.state = 'sale' AND so.date_order >= '%s' AND so.sale_order_return = true ORDER BY so.date_order asc" % (start_date,)
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    return_has_so.append(query_line[0])
            print "return_has_so = %s - %s" % (return_has_so, len(return_has_so))
            note += "return_has_so : " + ' ,'.join(line for line in return_has_so) + '\n'
            gia_von_id.add_note(note)

            return_no_so = []
            query = "SELECT DISTINCT so.name, so.date_order FROM sale_order so WHERE so.state = 'sale' AND so.sale_order_return = true AND so.name NOT IN ('%s') AND so.date_order >= '%s' ORDER BY so.date_order asc" % ("','".join(return_has_so), start_date)
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    return_no_so.append(query_line[0])
            print "return_no_so = %s - %s" % (return_no_so, len(return_no_so))
            note += "return_no_so : " + ' ,'.join(line for line in return_no_so) + '\n'
            gia_von_id.add_note(note)

            return_no_so_done = []
            query = "SELECT origin FROM stock_picking WHERE state = 'done' AND origin IN ('%s') AND min_date >= '%s' ORDER BY min_date asc" % ("','".join(return_no_so), start_date)
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    return_no_so_done.append(query_line[0])
            print "return_no_so_done = %s - %s" % (return_no_so_done, len(return_no_so_done))
            note += "return_no_so_done : " + ' ,'.join(line for line in return_no_so_done) + '\n'
            gia_von_id.add_note(note)

            so_has_return = []
            query = "SELECT DISTINCT so.name, so.date_order FROM sale_order_return_rel sr INNER JOIN sale_order so ON so.id = sr.sale_order_return_relation WHERE so.state = 'sale' AND so.date_order >= '%s' AND so.sale_order_return = false ORDER BY so.date_order asc" % (
            start_date)
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    so_has_return.append(query_line[0])
            print "so_has_return = %s - %s" % (so_has_return, len(so_has_return))
            note += "so_has_return : " + ' ,'.join(line for line in so_has_return) + '\n'
            gia_von_id.add_note(note)

            so_has_return_done = []
            query = "SELECT origin FROM stock_picking WHERE state = 'done' AND min_date >= '%s' AND origin IN ('%s') ORDER BY min_date asc" % (
            start_date, "','".join(so_has_return),)
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    so_has_return_done.append(query_line[0])
            print "so_has_return_done = %s - %s" % (so_has_return_done, len(so_has_return_done))
            note += "so_has_return_done : " + ' ,'.join(line for line in so_has_return_done) + '\n'
            gia_von_id.add_note(note)

            return_has_so_done = []
            query = "SELECT origin FROM stock_picking WHERE state = 'done' AND min_date >= '%s' AND origin IN ('%s') ORDER BY min_date asc" % (
            start_date, "','".join(return_has_so),)
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    return_has_so_done.append(query_line[0])
            print "return_has_so_done = %s - %s" % (return_has_so_done, len(return_has_so_done))
            note += "return_has_so_done : " + ' ,'.join(line for line in return_has_so_done) + '\n'
            gia_von_id.add_note(note)

            rtp_picking_dones = []
            query = "SELECT origin FROM stock_picking WHERE state = 'done' AND min_date >= '%s' AND origin LIKE '%s' ORDER BY min_date asc" % (
            start_date, 'RTP%')
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    rtp_picking_dones.append(query_line[0])
            print "rtp_picking_dones = %s - %s" % (rtp_picking_dones, len(rtp_picking_dones))
            note += "rtp_picking_dones : " + ' ,'.join(line for line in rtp_picking_dones) + '\n'
            gia_von_id.add_note(note)
            #
            rtp_picking_assigned = []
            query = "SELECT origin FROM stock_picking WHERE state IN ('assigned', 'partially_available') AND min_date >= '%s' AND origin LIKE '%s' ORDER BY min_date asc" % (
            start_date, 'RTP%')
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    rtp_picking_assigned.append(query_line[0])
            print "rtp_picking_assigned = %s - %s" % (rtp_picking_assigned, len(rtp_picking_assigned))
            note += "rtp_picking_assigned : " + ' ,'.join(line for line in rtp_picking_assigned) + '\n'
            gia_von_id.add_note(note)

            so_picking_dones = []
            query = "SELECT origin FROM stock_picking WHERE state = 'done' AND min_date >= '%s' AND origin LIKE '%s' ORDER BY min_date asc" % (
            start_date, 'SO%')
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    so_picking_dones.append(query_line[0])
            print "so_picking_dones = %s - %s" % (so_picking_dones, len(so_picking_dones))
            note += "so_picking_dones : " + ' ,'.join(line for line in so_picking_dones) + '\n'
            gia_von_id.add_note(note)

            so_picking_assigned = []
            query = "SELECT origin FROM stock_picking WHERE state IN ('assigned', 'partially_available') AND min_date >= '%s' AND origin LIKE '%s' ORDER BY min_date asc" % (
            start_date, 'SO%')
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    so_picking_assigned.append(query_line[0])
            print "so_picking_assigned = %s - %s" % (so_picking_assigned, len(so_picking_assigned))
            note += "so_picking_assigned : " + ' ,'.join(line for line in so_picking_assigned) + '\n'
            gia_von_id.add_note(note)

            so_picking_confirmed = []
            query = "SELECT origin FROM stock_picking WHERE state = 'confirmed' AND min_date >= '%s' AND origin LIKE '%s' ORDER BY min_date asc" % (
            start_date, 'SO%')
            print 'query - %s' % (query,)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    so_picking_confirmed.append(query_line[0])
            print "so_picking_confirmed = %s - %s" % (so_picking_confirmed, len(so_picking_confirmed))
            note += "so_picking_confirmed : " + ' ,'.join(line for line in so_picking_confirmed) + '\n'
            gia_von_id.add_note(note)

            # Step 1: Reset assigned, partial available SO
            reset_picking = []
            note += "Reset Picking : "
            print "Step 1: Reset returned has SO"
            if return_has_so_done and len(return_has_so_done) > 0:
                picking_ids = self.env['stock.picking'].search([('origin', 'in', return_has_so_done)],order='min_date desc')
                for picking_id in picking_ids:
                    print "Reset picking: %s" % (picking_id.id)
                    try:
                        picking_id.do_reset_stock_picking()
                    except Exception, e:
                        # print e
                        note += picking_id.name + ' %s ,' % (e)
                        gia_von_id.add_note(note)
                        print "ERROR --------------- Reset picking: %s" % (picking_id.id)
                        continue
                    note += picking_id.name + ' ,'
                    gia_von_id.add_note(note)

            # Step 2: Reset confirmed SO
            print "Step 2: Reset confirmed SO"
            if so_picking_dones and len(so_picking_dones) > 0:
                picking_ids = self.env['stock.picking'].search([('origin', 'in', so_picking_dones)],order='min_date desc')
                for picking_id in picking_ids:
                    print "Reset picking: %s" % (picking_id.id)
                    try:

                        picking_id.do_reset_stock_picking()
                    except Exception, e:
                        # print e
                        note += picking_id.name + ' %s ,' % (e)
                        gia_von_id.add_note(note)
                        print "ERROR --------------- Reset picking: %s" % (picking_id.id)
                        continue
                    note += picking_id.name + ' ,'
                    gia_von_id.add_note(note)

            # Step 3: Reset assigned, partial available SO
            print "Step 3: Reset assigned SO"
            if so_picking_assigned and len(so_picking_assigned) > 0:
                picking_ids = self.env['stock.picking'].search([('origin', 'in', so_picking_assigned)],order='min_date desc')
                for picking_id in picking_ids:
                    print "Reset picking: %s" % (picking_id.id)

                    try:
                        # confirm & validate the picking
                        picking_id.do_reset_stock_picking()
                    except Exception, e:
                        # print e
                        note += picking_id.name + ' %s ,'%(e)
                        gia_von_id.add_note(note)
                        print "ERROR --------------- Reset picking: %s" % (picking_id.id)
                        continue
                    note += picking_id.name + ' ,'
                    gia_von_id.add_note(note)

            # Step 4: SO has return done
            print "Step 4: SO has return done"
            if so_has_return_done and len(so_has_return_done) > 0:
                picking_ids = self.env['stock.picking'].search([('origin', 'in', so_has_return_done)],order='min_date desc')
                for picking_id in picking_ids:
                    print "Reset picking: %s" % (picking_id.id)
                    query = "UPDATE stock_move SET state='draft' WHERE picking_id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    query = "UPDATE stock_picking SET state='draft' WHERE id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)
                    try:
                        # Confirm the picking
                        picking_id.action_confirm()
                        picking_id.do_new_transfer()

                    except Exception, e:
                        # print e
                        note += picking_id.name + ' %s ,' % (e)
                        gia_von_id.add_note(note)
                        print "ERROR --------------- Reset picking: %s" % (picking_id.id)
                        continue
                    note += picking_id.name + ' ,'
                    gia_von_id.add_note(note)

            # Step 5: return has so done
            print "Step5: return has so done"
            if return_has_so_done and len(return_has_so_done) > 0:
                picking_ids = self.env['stock.picking'].search([('origin', 'in', return_has_so_done)],order='min_date asc')
                for picking_id in picking_ids:
                    print "Reset picking: %s" % (picking_id.id)

                    query = "UPDATE stock_move SET state='draft' WHERE picking_id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    query = "UPDATE stock_picking SET state='draft' WHERE id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    try:
                        # Confirm the picking
                        picking_id.action_confirm()
                        picking_id.with_context(sale_order_return=True).action_assign()
                        picking_id.do_new_transfer()
                    except Exception, e:
                        # print e
                        note += picking_id.name + ' %s ,' % (e)
                        gia_von_id.add_note(note)
                        print "ERROR --------------- Reset picking: %s" % (picking_id.id)
                        continue
                    note += picking_id.name + ' ,'
                    gia_von_id.add_note(note)

            # Step6: Purchase return assigned
            print "Step6: Purchase return assigned"
            if rtp_picking_assigned and len(rtp_picking_assigned) > 0:
                picking_ids = self.env['stock.picking'].search([('origin', 'in', rtp_picking_assigned)],order='min_date asc')
                for picking_id in picking_ids:
                    print "Reset picking: %s" % (picking_id.id)
                    query = "UPDATE stock_move SET state='draft' WHERE picking_id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    query = "UPDATE stock_picking SET state='draft' WHERE id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    try:
                        # Confirm the picking
                        picking_id.action_confirm()
                    except Exception, e:
                        # print e
                        note += picking_id.name + ' %s ,' % (e)
                        gia_von_id.add_note(note)
                        print "ERROR --------------- Reset picking: %s" % (picking_id.id)
                        continue
                    note += picking_id.name + ' ,'
                    gia_von_id.add_note(note)

            # Step7: So picking done
            print "Step7: So picking done"
            if so_picking_dones and len(so_picking_dones) > 0:
                arguments = [
                    ('origin', 'in', so_picking_dones),
                ]
                if so_has_return_done and len(so_has_return_done) > 0:
                    arguments.append(('origin', 'not in', so_has_return_done))
                picking_ids = self.env['stock.picking'].search(arguments,order='min_date asc')
                for picking_id in picking_ids:
                    print "Reset picking: %s" % (picking_id.id)
                    query = "UPDATE stock_move SET state='draft' WHERE picking_id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    query = "UPDATE stock_picking SET state='draft' WHERE id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    try:
                        # Confirm the picking
                        picking_id.action_confirm()
                        picking_id.do_new_transfer()

                    except Exception, e:
                        # print e
                        note += picking_id.name + ' %s ,' % (e)
                        gia_von_id.add_note(note)
                        print "ERROR --------------- Reset picking: %s" % (picking_id.id)
                        continue
                    note += picking_id.name + ' ,'
                    gia_von_id.add_note(note)

            # Step8: So picking assign
            print "Step8: So picking assign"
            if so_picking_assigned and len(so_picking_assigned) > 0:
                picking_ids = self.env['stock.picking'].search([('origin', 'in', so_picking_assigned)], order='min_date asc')
                for picking_id in picking_ids:
                    print "Reset picking: %s" % (picking_id.id)

                    query = "UPDATE stock_move SET state='draft' WHERE picking_id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    query = "UPDATE stock_picking SET state='draft' WHERE id = %s" % (picking_id.id,)
                    self.env.cr.execute(query)

                    try:
                        # Confirm the picking
                        picking_id.action_confirm()
                    except Exception, e:
                        # print e
                        note += picking_id.name + ' %s ,' % (e)
                        gia_von_id.add_note(note)
                        print "ERROR --------------- Reset picking: %s" % (picking_id.id)
                        continue
                    note += picking_id.name + ' ,'
                    gia_von_id.add_note(note)

            query = "UPDATE account_move SET date = stock_picking.min_date FROM stock_picking WHERE stock_picking.name = account_move.ref AND account_move.ref IS NOT NULL AND account_move.ref LIKE 'WH/OUT/%'"
            self.env.cr.execute(query)

            query = "UPDATE account_move_line SET date = account_move.date FROM account_move WHERE account_move.id = account_move_line.move_id AND account_move.ref IS NOT NULL AND account_move.ref LIKE 'WH/OUT/%'"
            self.env.cr.execute(query)

            query = "UPDATE account_move SET date = stock_picking.min_date FROM stock_picking WHERE stock_picking.name = account_move.ref AND account_move.ref IS NOT NULL AND account_move.ref LIKE 'WH/IN/%'"
            self.env.cr.execute(query)

            query = "UPDATE account_move_line SET date = account_move.date FROM account_move WHERE account_move.id = account_move_line.move_id AND account_move.ref IS NOT NULL AND account_move.ref LIKE 'WH/IN/%'"
            self.env.cr.execute(query)

            # Step-1: Enable cron picking
            print "Step-1: Enable cron picking"
            query = "UPDATE ir_cron SET active=true WHERE name = '%s'" % ('Cron Create Picking From Sale',)
            self.env.cr.execute(query)

            query = "UPDATE ir_cron SET active=true WHERE name = '%s'" % ('Update Picking To Confirm',)
            self.env.cr.execute(query)

            query = "UPDATE ir_cron SET active=true WHERE name = '%s'" % ('Save Picking History',)
            self.env.cr.execute(query)

            # Final Step Set Done for Sale,Purchase
            if start_date and end_date:
                query_update_so = "UPDATE sale_order SET state = 'done' where state = 'sale' and date_order >= '%s' and date_order <= '%s'" % (
                    start_date, end_date)
                self.env.cr.execute(query_update_so)

                query_update_po = "UPDATE purchase_order SET state = 'done' where state = 'purchase' and date_order >= '%s' and date_order <= '%s'" % (
                    start_date, end_date)
                self.env.cr.execute(query_update_po)

            print "\nEND time:", datetime.datetime.today()

            gia_von_id.write({'state': 'done','complete_date':datetime.datetime.now()})
            self.env.ref('tuanhuy_gia_von.cron_update_state_tinh_gia_von').sudo().write({'active': True, 'nextcall': datetime.datetime.now() + timedelta(minutes=3)})

    @api.multi
    def update_state_cron_gia_von(self):
        gia_von_next = self.env['gia.von.popup'].search([('state', '=', 'schedule')], limit=1, order='doing_date asc')
        if gia_von_next:
            self.env.ref('tuanhuy_gia_von.cron_tinh_gia_von').sudo().write({'active': True, 'nextcall': self.doing_date, 'args': str(tuple(gia_von_next.ids))})
        else:
            self.env.ref('tuanhuy_gia_von.cron_tinh_gia_von').sudo().write({'active': False})