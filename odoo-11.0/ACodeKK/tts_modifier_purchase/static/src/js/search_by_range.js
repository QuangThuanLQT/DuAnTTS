odoo.define('purchase_search_by_range.tree', function (require) {
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
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    var NewListView = require('search_by_date_range.tree');
    ListView.include({

        init: function (parent, action) {
            this.actionManager = parent;
            this.controller_url = action.context.url;
            this.report_model = action.context.model;
            // in case of a financial report, an id is defined in the action declaration
            this.report_id = action.context.id ? parseInt(action.context.id, 10) : undefined;
            this.given_context = {};
            if (action.context.context) {
                this.given_context = action.context.context;
            }
            this.given_context.from_report_id = action.context.from_report_id;
            this.given_context.from_report_model = action.context.from_report_model;
            this.given_context.force_account = action.context.force_account;
            this.given_context.active_id = action.context.active_id;
            this.odoo_context = action.context;
            return this._super.apply(this, arguments);
        },

        render_buttons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            if (self.model == 'purchase.order' && (self.ViewManager.action.xml_id == 'purchase.purchase_rfq' ||
                self.ViewManager.action.xml_id == 'purchase.purchase_form_action' ||
                self.ViewManager.action.xml_id == 'sale_purchase_returns.purchase_order_return_action')) {

                self.purchase_export_over = $(QWeb.render('purchase_export_over', {}));
                self.purchase_export_over.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/purchase_export_data_over',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.purchase_export_detail = $(QWeb.render('purchase_export_detail', {}));
                self.purchase_export_detail.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/purchase_export_data_detail',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_purchase_overview').length == 0) {
                    self.$buttons.append(self.purchase_export_over);
                }
                if (self.$buttons[0].getElementsByClassName('o_purchase_detail').length == 0) {
                    self.$buttons.append(self.purchase_export_detail)
                }


                sky_fields = [];
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.name === "user_id") {
                        sky_fields.push([value.name, value.string]);
                    }
                });
                if (sky_fields.length > 0) {
                    self.$search_user_id = $(QWeb.render('SkyERP.SearchUser', {'sky_fields': sky_fields}))
                    self.$search_user_id.find('.sky_user_id').on('change', function () {
                        self.tgl_search();
                    });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.cl_show_credit_debit').length > 0) {
                        self.$search_user_id.appendTo($('.cl_show_credit_debit'));
                    } else {
                        setTimeout(function () {
                            self.$search_user_id.appendTo($('.cl_show_credit_debit'));
                        }, 1000);
                    }
                }
                sky_fields = [];
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.name === "product_line_id") {
                        sky_fields.push([value.name, value.string]);
                    }
                });
                if (sky_fields.length > 0) {
                    self.$search_product_id = $(QWeb.render('SkyERP.SearchProduct', {'sky_fields': sky_fields}))
                    self.$search_product_id.find('.sky_product_id').on('change', function () {
                        self.tgl_search();
                    });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.cl_show_credit_debit').length > 0) {
                        self.$search_product_id.appendTo($('.cl_show_credit_debit'));
                    } else {
                        setTimeout(function () {
                            self.$search_product_id.appendTo($('.cl_show_credit_debit'));
                        }, 1000);
                    }
                }
                if (self.ViewManager.action.xml_id == 'purchase.purchase_rfq' || self.ViewManager.action.xml_id == 'purchase.purchase_form_action') {
                    sky_fields = [];
                    _.each(self.columns, function (value, key, list) {
                        if (value.string && value.string.length > 1 && value.name === "state") {
                            sky_fields.push([value.name, value.string]);
                        }
                    });
                    if (sky_fields.length > 0) {
                        self.$search_state = $(QWeb.render('SkyERP.SearchState', {'sky_fields': sky_fields}))
                        self.$search_state.find('.sky_state').on('change', function () {
                            self.tgl_search();
                        });
                        // self.$search_customer.appendTo($('.cl_search_by_range'));
                        if ($('.cl_show_credit_debit').length > 0) {
                            self.$search_state.appendTo($('.cl_show_credit_debit'));
                        } else {
                            setTimeout(function () {
                                self.$search_state.appendTo($('.cl_show_credit_debit'));
                            }, 1000);
                        }
                    }
                    sky_fields = [];
                    _.each(self.columns, function (value, key, list) {
                        if (value.string && value.string.length > 1 && value.name === "operation_state") {
                            sky_fields.push([value.name, value.string]);
                        }
                    });
                    if (sky_fields.length > 0) {
                        self.$purchase_operation_state = $(QWeb.render('SkyERP.PurchaseOperaionState', {'sky_fields': sky_fields}))
                        self.$purchase_operation_state.find('.sky_state').on('change', function () {
                            self.tgl_search();
                        });
                        // self.$search_customer.appendTo($('.cl_search_by_range'));
                        if ($('.cl_show_credit_debit').length > 0) {
                            self.$purchase_operation_state.appendTo($('.cl_show_credit_debit'));
                        } else {
                            setTimeout(function () {
                                self.$purchase_operation_state.appendTo($('.cl_show_credit_debit'));
                            }, 1000);
                        }
                    }


                }

                if (self.ViewManager.action.xml_id == 'sale_purchase_returns.purchase_order_return_action') {
                    sky_fields = [];
                    _.each(self.columns, function (value, key, list) {
                        if (value.string && value.string.length > 1 && value.name === "state_return") {
                            sky_fields.push([value.name, value.string]);
                        }
                    });
                    if (sky_fields.length > 0) {
                        self.$search_state = $(QWeb.render('SkyERP.PurchaseStateReturn', {'sky_fields': sky_fields}))
                        self.$search_state.find('.sky_state').on('change', function () {
                            self.tgl_search();
                        });
                        // self.$search_customer.appendTo($('.cl_search_by_range'));
                        if ($('.cl_show_credit_debit').length > 0) {
                            self.$search_state.appendTo($('.cl_show_credit_debit'));
                        } else {
                            setTimeout(function () {
                                self.$search_state.appendTo($('.cl_show_credit_debit'));
                            }, 1000);
                        }
                    }

                    sky_fields = [];
                    _.each(self.columns, function (value, key, list) {
                        if (value.string && value.string.length > 1 && value.name === "operation_state") {
                            sky_fields.push([value.name, value.string]);
                        }
                    });
                    if (sky_fields.length > 0) {
                        self.$purchase_operation_state = $(QWeb.render('SkyERP.PurchaseOperaionStateReturn', {'sky_fields': sky_fields}))
                        self.$purchase_operation_state.find('.sky_state').on('change', function () {
                            self.tgl_search();
                        });
                        // self.$search_customer.appendTo($('.cl_search_by_range'));
                        if ($('.cl_show_credit_debit').length > 0) {
                            self.$purchase_operation_state.appendTo($('.cl_show_credit_debit'));
                        } else {
                            setTimeout(function () {
                                self.$purchase_operation_state.appendTo($('.cl_show_credit_debit'));
                            }, 1000);
                        }
                    }

                }


            }


        },

        tgl_search: function () {
            var self = this;
            var domain = self.dataset.domain;
            if (self.$search_user_id) {
                var user_name = self.$search_user_id.find('.sky_user_id').val()
                if (user_name) {
                    new Model("res.users").call("search_user_order", [user_name]).then(function (result) {
                        domain.push(['user_id', 'in', result]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }

            }
            if (self.$search_product_id) {
                var product_str = self.$search_product_id.find('.sky_product_id').val()
                if (product_str) {
                    new Model("product.product").call("search_product_name", [product_str]).then(function (result) {
                        domain.push(['product_id', 'in', result]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }
            }
            if (self.$search_state && self.model == 'purchase.order') {
                var state = self.$search_state.find('.sky_state').val()
                if (state) {
                    domain.push(['state', '=', state]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
            if (self.$purchase_operation_state) {
                var state = self.$purchase_operation_state.find('.sky_state').val()
                if (state) {
                    new Model("purchase.order").call("search_operation_state", [state]).then(function (result) {
                        domain.push(['id', 'in', result]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }
            }
            this._super.apply(this, arguments);

        },
    });


    FormView.include({
        load_record: function (record) {
            var self = this;
            if (self.model == 'purchase.order') {
                var self = this;
                if (self.get_fields_values().state == 'purchase' || self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
                    setTimeout(function () {
                        $(".o_form_button_edit").removeClass('hidden');
                    }, 400)
                }
            }
            self._super.apply(self, arguments);
            if (self.get_fields_values().state == 'sale' || self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
                setTimeout(function () {
                    $(".o_form_button_edit").removeClass('hidden');
                }, 500)
            }
            // if (self.model == 'sale.order' && self.ViewManager.action.xml_id == 'sale.action_orders') {
            //     setTimeout(function () {
            //         $(".o_form_button_create").addClass('hidden');
            //     }, 400)
            //     setTimeout(function () {
            //         $(".o_cp_sidebar li:contains('Xóa')").addClass('hidden');
            //     }, 400)
            //     setTimeout(function () {
            //         $(".o_cp_sidebar li:contains('Sao chép')").addClass('hidden');
            //     }, 400)
            //     setTimeout(function () {
            //         $(".o_cp_sidebar li:contains('Tạo Hoá Đơn')").addClass('hidden');
            //     }, 400)
            //     setTimeout(function () {
            //         $(".o_cp_sidebar li:contains('Cập Nhật Hoá Đơn')").addClass('hidden');
            //     }, 400)
            //     setTimeout(function () {
            //         $(".o_cp_sidebar li:contains('Tạo Giao Hàng')").addClass('hidden');
            //     }, 400)
            //     setTimeout(function () {
            //         $(".o_cp_sidebar li:contains('Cập Nhật Mới Hoá Đơn')").addClass('hidden');
            //     }, 400)
            //     setTimeout(function () {
            //         $(".o_cp_sidebar li:contains('Huỷ kiểm tra')").addClass('hidden');
            //     }, 400)
            //
            //     if (self.get_fields_values().state == 'sale' || self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
            //         setTimeout(function () {
            //             $(".o_form_button_edit").removeClass('hidden');
            //         }, 500)
            //     }
            // }

            if (self.model == 'purchase.order') {
                var self = this;
                if (self.get_fields_values().state == 'purchase' || self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
                    setTimeout(function () {
                        $(".o_form_button_edit").removeClass('hidden');
                    }, 400)
                    if (self.get_fields_values().operation_state == 'done') {
                        setTimeout(function () {
                            $(".o_form_button_edit").addClass('hidden');
                        }, 400)
                    }
                }
            }
        },
    });
});