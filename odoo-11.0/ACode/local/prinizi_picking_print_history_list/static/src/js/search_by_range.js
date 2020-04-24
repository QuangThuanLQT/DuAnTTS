odoo.define('prinizi_picking_print_history_list.tree', function (require) {
    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var QWeb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;
    // var checkState = false;

    ListView.include({
        render_buttons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);

            if (self.model == 'stock.picking' && (self.ViewManager.action.xml_id == 'prinizi_picking_print_history_list.picking_print_history_action')) {

                $('o_picking_delivery_print_excel').addClass('hidden')
                self.prinizi_lich_su_in_print = $(QWeb.render('prinizi_lich_su_in_print', {}));
                self.prinizi_lich_su_in_print.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/picking_lich_su_in_export',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_prinizi_lich_su_in_print').length == 0) {
                     setTimeout(function () {
                         self.$buttons.append(self.prinizi_lich_su_in_print)
                     }, 100);
                }
            }
        }
    });
});