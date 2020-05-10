odoo.define('cptuanhuy_coa.tree', function (require) {
    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;
    var TreeView = require('web.TreeView');

    TreeView.include({
        getdata: function(id, children_ids) {
            var self = this;
            var res = this._super(id, children_ids);

            if (self.model == 'account.account') {
                console.log('account.account');
                var check = true;
                if (check == true) {
                    self.$before_debit_number = $(QWeb.render('Account.BeforeDebitNumber', {}));
                    self.$ps_debit_credit = $(QWeb.render('Account.PSDebitCredit', {}));
                    self.$last_debit_credit = $(QWeb.render('Account.LastDebitCredit', {}));
                    self.$button_print_account = $(QWeb.render('Account.buttons_print', {}));
                    self.$button_print_account.click(function () {
                        var domain_list = self.dataset.domain;
                        var start_date = false;
                        var end_date = false;
                        if (self.$search_button) {
                            start_date = self.$search_button.find('.sky_start_date').val();
                            end_date = self.$search_button.find('.sky_end_date').val();
                        }

                        framework.blockUI();
                        self.dataset.read_ids(children_ids, self.fields_list()).done(function(records) {
                        new Model("account.account").call("print_excel", [records]).then(function (result) {
                                session.get_file({
                                    url: result,
                                    dataType: 'json',
                                    data: {
                                    },
                                    complete: framework.unblockUI,
                                    error: crash_manager.rpc_error.bind(crash_manager),
                                });
                            });
                        });
                    });
                    if (!$('.sky_debit_number').length) {
                        if ($('.o_treeview_table').length > 0) {
                            self.$before_debit_number.insertBefore($('.o_treeview_table'));
                            self.$ps_debit_credit.insertBefore($('.o_treeview_table'));
                            self.$last_debit_credit.insertBefore($('.o_treeview_table'));
                            self.$button_print_account.insertBefore($('.o_treeview_table'));
                        } else {
                            setTimeout(function () {
                                self.$before_debit_number.insertBefore($('.o_treeview_table'));
                                self.$ps_debit_credit.insertBefore($('.o_treeview_table'));
                                self.$last_debit_credit.insertBefore($('.o_treeview_table'));
                                self.$button_print_account.insertBefore($('.o_treeview_table'));
                            }, 1000);
                        }
                    }
                    self.dataset.read_ids(children_ids, this.fields_list()).done(function(records) {
                        var total_before_debit = total_before_credit = total_current_debit = total_current_credit = total_after_debit = total_after_credit = 0;
                        _(records).each(function (record) {

                            total_before_debit += record.before_debit;
                            total_before_credit += record.before_credit;
                            total_current_debit += record.current_debit;
                            total_current_credit += record.current_credit;
                            total_after_debit += record.after_debit;
                            total_after_credit += record.after_credit;
                        });
                        $('.sky_debit_number').css('width' , '150px');
                        $('.sky_credit_number').css('width' , '150px');
                        $('.sky_debit_number_ps').css('width' , '150px');
                        $('.sky_credit_number_ps').css('width' , '150px');
                        $('.sky_debit_number_last').css('width' , '150px');
                        $('.sky_credit_number_last').css('width' , '150px');

                        $('.sky_debit_number').val(total_before_debit.toFixed(2));
                        $('.sky_credit_number').val(total_before_credit.toFixed(2));
                        $('.sky_debit_number_ps').val(total_current_debit.toFixed(2));
                        $('.sky_credit_number_ps').val(total_current_credit.toFixed(2));
                        $('.sky_debit_number_last').val(total_after_debit.toFixed(2));
                        $('.sky_credit_number_last').val(total_after_credit.toFixed(2));
                    })

                }

            }
            return res;

        },
    });


});