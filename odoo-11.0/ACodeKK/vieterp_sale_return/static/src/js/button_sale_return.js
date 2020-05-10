odoo.define('vieterp_sale_return.button_sale_return', function (require) {
    "use strict";

    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var _t = core._t;
    var QWeb = core.qweb;
    var FormView = require('web.FormView');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');


    ListView.include({

        render_buttons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            self.$buttons.find('.o_sale_return_excel').remove();
            if (self.model == 'sale.order' && (self.ViewManager.action.xml_id == 'sale.action_quotations'
                || self.ViewManager.action.xml_id == 'sale.action_orders'
                || self.ViewManager.action.xml_id == 'vieterp_sale_return.order_return_action')) {
                self.$sale_return_print = $(QWeb.render('sale_return_print', {}));

                self.$sale_return_print.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_sale_return_excel',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.$buttons.append(self.$sale_return_print)

                self.$sale_return_detail_print = $(QWeb.render('sale_return_detail_print', {}));

                self.$sale_return_detail_print.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_sale_return_detail_excel',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.$buttons.append(self.$sale_return_detail_print)

            }

        },

    });

});