odoo.define('tuanhuy_purchase_search_by_date_range.tree', function (require) {
    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    var NewListView = require('search_by_date_range.tree');

    ListView.include({
        render_buttons: function () {
            var self = this;
            this._super.apply(this, arguments);
            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.string && value.string.length > 1) {
                    sky_fields.push([value.name, value.string]);
                }
            });

            if (self.model == 'purchase.order.line'){
                self.$button_print_excel = $(QWeb.render('SkyERP.Account_131', {'sky_fields': sky_fields}));
                if ($('.cl_search_by_range').length > 0) {
                        self.$button_print_excel.appendTo($('.cl_search_by_range'));
                    }
                else {
                        setTimeout(function () {
                            self.$button_print_excel.appendTo($('.cl_search_by_range'));
                        }, 1000);
                    }
                self.$button_print_excel.click(function () {

                        var domain_list = self.dataset.domain;
                        var partner_str = false;
                        var start_date = false;
                        var end_date = false;
                        if (self.$search_customer) {
                            partner_str = self.$search_customer.find('.sky_customer_name').val()
                        }
                        if (self.$search_button) {
                            start_date = self.$search_button.find('.sky_start_date').val();
                            end_date = self.$search_button.find('.sky_end_date').val();
                        }

                        framework.blockUI();
                        var data = {
                            start_date: start_date,
                            end_date: end_date,
                        };
                        var pol_model = new Model('purchase.order.line');
                        var ids =  pol_model.call('search',[domain_list]).then(function (record) {
                           return  record.id
                        });

                        for (var i =0;i< domain_list.length;i++){
                            data[domain_list[i][0]] = domain_list[i]
                        }
                        session.get_file({
                            url: '/print_purchase_order_line',
                            dataType: 'json',
                            data: data,
                            complete: framework.unblockUI,
                            error: crash_manager.rpc_error.bind(crash_manager),
                        });


                    });
            }
        }
    })

});