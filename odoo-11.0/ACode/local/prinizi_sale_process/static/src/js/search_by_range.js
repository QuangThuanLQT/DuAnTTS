odoo.define('prinizi_sale_process.tree', function (require) {
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

            if (self.model == 'stock.picking' && self.ViewManager.action.xml_id == 'prinizi_sale_process.stock_picking_internal_sale_action_picking_type') {

                self.prinizi_internal_sale_export_overview = $(QWeb.render('prinizi_internal_sale_export_overview', {}));
                self.prinizi_internal_sale_export_overview.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/prinizi_internal_sale_export_overview',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_prinizi_internal_sale_overview').length == 0) {
                     setTimeout(function () {
                         self.$buttons.append(self.prinizi_internal_sale_export_overview)
                     }, 100);
                }

                self.prinizi_internal_sale_export_detail = $(QWeb.render('prinizi_internal_sale_export_detail', {}));
                self.prinizi_internal_sale_export_detail.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/prinizi_internal_sale_export_detail',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_prinizi_internal_sale_detail').length == 0) {
                     setTimeout(function () {
                         self.$buttons.append(self.prinizi_internal_sale_export_detail)
                     }, 100);
                }

                setTimeout(function () {
                    $('.o_picking_receipt_print_excel').addClass('hidden')
                    $('.o_picking_delivery_print_excel').addClass('hidden')
                    }, 200);
                setTimeout(function () {
                    $('.tts_select_source_location_field').addClass('hidden')
                    $('.tts_source_location_name').addClass('hidden')
                    $('.tts_select_dest_location_field').addClass('hidden')
                    $('.tts_dest_location_name').addClass('hidden')
                }, 1000);
            }
        }
    });
});