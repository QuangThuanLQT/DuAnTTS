odoo.define('tts_search_by_range.tree', function (require) {
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
    // var checkState = false;
    var domainRemove = [];
    var NewListView = require('search_by_date_range.tree');
    ListView.include({

        load_list: function () {
            var self = this;
            var result = self._super();
            setTimeout(function () {
                $(".breadcrumb li:contains('Trả Hàng Bán')").css('background-color', '#f0eeee');
                $(".breadcrumb li:contains('Trả Hàng Mua')").css('background-color', '#f0eeee');
            }, 300)
            return result;
        },

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
            console.log('run 2 tts');
            if (self.$search_button && self.model == 'account.invoice.line') {
                setTimeout(function () {
                    var start_date = self.$search_button.find('.sky_start_date'),
                        end_date = self.$search_button.find('.sky_end_date')

                    var today = new Date();
                    var dd = String(today.getDate()).padStart(2, '0');
                    var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
                    var yyyy = today.getFullYear();

                    today = dd + '/' + mm + '/' + yyyy;

                    start_date.val(today)
                    end_date.val(today)

                    start_date.trigger('change');
                    end_date.trigger('change');
                }, 2000);
            }
            if (self.model == 'sale.order' && (self.ViewManager.action.xml_id == 'sale.action_quotations'
                || self.ViewManager.action.xml_id == 'sale.action_orders'
                || self.ViewManager.action.xml_id == 'sale_purchase_returns.sale_order_return_action')) {

                self.sale_export_over = $(QWeb.render('sale_export_over', {}));
                self.sale_export_over.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/sale_export_data_over',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.sale_export_detail = $(QWeb.render('sale_export_detail', {}));
                self.sale_export_detail.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/sale_export_data_detail',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_sale_overview').length == 0) {
                    self.$buttons.append(self.sale_export_over);
                }
                if (self.$buttons[0].getElementsByClassName('o_sale_detail').length == 0) {
                    self.$buttons.append(self.sale_export_detail)
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
                if (self.ViewManager.action.xml_id == 'sale.action_orders') {
                    sky_fields = [];
                    _.each(self.columns, function (value, key, list) {
                        if (value.string && value.string.length > 1 && value.name === "city") {
                            sky_fields.push([value.name, value.string]);
                        }
                    });
                    if (sky_fields.length > 0) {
                        self.$search_city = $(QWeb.render('SkyERP.SearchCity', {'sky_fields': sky_fields}))
                        self.$search_city.find('.search_city').on('change', function () {
                            self.tgl_search_city();
                        });
                        if ($('.cl_show_credit_debit').length > 0) {
                            self.$search_city.appendTo($('.cl_show_credit_debit'));
                        } else {
                            setTimeout(function () {
                                self.$search_city.appendTo($('.cl_show_credit_debit'));
                            }, 1000);
                        }
                    }
                    new Model("sale.order").call("get_city_list", []).then(function (city_ids) {
                        sbr_autocomplete(self.$search_city.find('#input_city_name')[0], city_ids);
                    });
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

                sky_fields = [];
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.name === "state") {
                        sky_fields.push([value.name, value.string]);
                    }
                });
                if (sky_fields.length > 0) {
                    self.$search_state = $(QWeb.render('SkyERP.SaleState', {'sky_fields': sky_fields}))
                    self.$search_state.find('.sky_state').on('change', function () {
                        // checkState = true;
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

                if (self.ViewManager.action.xml_id == 'sale.action_orders') {
                    sky_fields = [];
                    _.each(self.columns, function (value, key, list) {
                        if (value.string && value.string.length > 1 && value.name === "trang_thai_dh") {
                            sky_fields.push([value.name, value.string]);
                        }
                    });
                    if (sky_fields.length > 0) {
                        self.$search_operation_state_sale_order = $(QWeb.render('SkyERP.SearchOperaionStateSaleOrder', {'sky_fields': sky_fields}))
                        self.$search_operation_state_sale_order.find('.sky_state_dh').on('change', function () {
                            self.tgl_search();
                        });
                        // self.$search_customer.appendTo($('.cl_search_by_range'));
                        if ($('.cl_show_credit_debit').length > 0) {
                            self.$search_operation_state_sale_order.appendTo($('.cl_show_credit_debit'));
                        } else {
                            setTimeout(function () {
                                self.$search_operation_state_sale_order.appendTo($('.cl_show_credit_debit'));
                            }, 1000);
                        }
                    }
                }

                if (self.ViewManager.action.xml_id == 'sale_purchase_returns.sale_order_return_action') {
                    sky_fields = [];
                    _.each(self.columns, function (value, key, list) {
                        if (value.string && value.string.length > 1 && value.name === "trang_thai_dh") {
                            sky_fields.push([value.name, value.string]);
                        }
                    });
                    if (sky_fields.length > 0) {
                        self.$search_operation_state = $(QWeb.render('SkyERP.SearchOperaionState', {'sky_fields': sky_fields}))
                        self.$search_operation_state.find('.sky_state').on('change', function () {
                            self.tgl_search();
                        });
                        // self.$search_customer.appendTo($('.cl_search_by_range'));
                        if ($('.cl_show_credit_debit').length > 0) {
                            self.$search_operation_state.appendTo($('.cl_show_credit_debit'));
                        } else {
                            setTimeout(function () {
                                self.$search_operation_state.appendTo($('.cl_show_credit_debit'));
                            }, 1000);
                        }
                    }
                }
            }
            if (self.model == 'account.invoice') {
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
            // if (self.$search_state && self.model == 'sale.order' && checkState == true) {
            if (self.$search_state && self.model == 'sale.order') {
                var state = self.$search_state.find('.sky_state').val()
                if (state) {
                    // for( var i=domain.length - 1; i>=0; i--){
                    //     if(domain[i] && (domain[i][0] === domainRemove[0]) && (domain[i][1] === domainRemove[1]) && (domain[i][2] === domainRemove[2])) {
                    //         domain.splice(i, 1);
                    //     }
                    // }
                    domain.push(['state', '=', state]);
                    // domainRemove = ['state', '=', state];
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    // checkState = false;
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
            if (self.$search_operation_state) {
                var state = self.$search_operation_state.find('.sky_state').val()
                if (state) {
                    new Model("sale.order").call("search_operation_state", [state]).then(function (result) {
                        domain.push(['id', 'in', result]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }
            }

            if (self.$search_operation_state_sale_order) {
                var trang_thai_dh = self.$search_operation_state_sale_order.find('.sky_state_dh').val()
                if (trang_thai_dh) {
                    for (var i = domain.length - 1; i >= 0; i--) {
                        if (domain[i] && (domain[i][0] === domainRemove[0]) && (domain[i][1] === domainRemove[1]) && (domain[i][2] === domainRemove[2])) {
                            domain.splice(i, 1);
                        }
                    }
                    new Model("sale.order").call("search_operation_state_sale_order", [trang_thai_dh]).then(function (result) {
                        domain.push(['id', 'in', result]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        domainRemove = ['id', 'in', result];
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }
            }
            this._super.apply(this, arguments);

        },
        tgl_search_city: function () {
            var self = this;
            var city_name = self.$search_city.find('.search_city').val();
            var domain = []
            if (city_name) {
                new Model('sale.order').call('get_search_city', [city_name]).then(function (city) {
                    domain.push(['id', 'in', city]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                });
            }
        },
    });


    FormView.include({
        do_onchange: function (widget) {
            var self = this;
            if (self._onchange_specs === undefined) {
                self._build_onchange_specs();
            }
            var onchange_specs = self._onchange_specs;
            try {
                var def = $.when({});
                var change_spec = widget ? onchange_specs[widget.name] : null;
                if (!widget || (!_.isEmpty(change_spec) && change_spec !== "0")) {
                    var ids = []
                        , trigger_field_name = widget ? widget.name : self._onchange_fields
                        , values = self._get_onchange_values()
                        , context = new data.CompoundContext(self.dataset.get_context());
                    if (widget && widget.build_context()) {
                        context.add(widget.build_context());
                    }
                    if (self.dataset.parent_view) {
                        var parent_name = self.dataset.parent_view.get_field_desc(self.dataset.child_name).relation_field;
                        context.add({
                            field_parent: parent_name
                        });
                    }
                    if (self.datarecord.id && !data.BufferedDataSet.virtual_id_regex.test(self.datarecord.id)) {
                        ids.push(self.datarecord.id);
                    }
                    if ((self.model == 'sale.order') && (trigger_field_name == 'order_line') || (self.model == 'purchase.order') && (trigger_field_name == 'order_line') ||
                        (self.model == 'stock.inventory') && (trigger_field_name == 'line_ids')) {
                    }
                    else {
                        def = self.alive(self.dataset.call("onchange", [ids, values, trigger_field_name, onchange_specs, context]));
                    }

                }
                this.onchanges_mutex.exec(function () {
                    return def.then(function (response) {
                        var fields = {};
                        if (widget) {
                            fields[widget.name] = widget.field;
                        } else {
                            fields = self.fields_view.fields;
                        }
                        var defs = [];
                        _.each(fields, function (field, fieldname) {
                            if (field && field.change_default) {
                                var value_;
                                if (response.value && (fieldname in response.value)) {
                                    value_ = response.value[fieldname];
                                } else {
                                    value_ = self.fields[fieldname].get_value();
                                }
                                var condition = fieldname + '=' + value_;
                                if (value_) {
                                    defs.push(self.alive(new Model('ir.values').call('get_defaults', [self.model, condition])).then(function (results) {
                                        if (!results.length) {
                                            return response;
                                        }
                                        if (!response.value) {
                                            response.value = {};
                                        }
                                        for (var i = 0; i < results.length; ++i) {
                                            var triplet = results[i];
                                            response.value[triplet[1]] = triplet[2];
                                        }
                                        return response;
                                    }));
                                }
                            }
                        });
                        return _.isEmpty(defs) ? response : $.when.apply(null, defs);
                    }).then(function (response) {
                        return self.on_processed_onchange(response);
                    });
                });
                return this.onchanges_mutex.def;
            } catch (e) {
                console.error(e);
                crash_manager.show_message(e);
                return $.Deferred().reject();
            }
        },
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);
            if (self.model == 'sale.order') {
                if (self.get_fields_values().trang_thai_dh && (self.get_fields_values().trang_thai_dh == 'delivery'
                    || self.get_fields_values().trang_thai_dh == 'done' || self.get_fields_values().trang_thai_dh == 'reverse_tranfer'
                    || self.get_fields_values().trang_thai_dh == 'cancel')) {

                    setTimeout(function () {
                        $(".o_form_button_edit").addClass('hidden');
                    }, 800)

                }
                else {

                    setTimeout(function () {
                        $(".o_form_button_edit").removeClass('hidden');
                    }, 800)
                }
            }
            if (self.model == 'sale.order' && self.ViewManager.action.xml_id == 'sale.action_orders') {
                setTimeout(function () {
                    $(".o_form_button_create").addClass('hidden');
                }, 400)
                setTimeout(function () {
                    $(".o_cp_sidebar li:contains('Xóa')").addClass('hidden');
                }, 400)
                setTimeout(function () {
                    $(".o_cp_sidebar li:contains('Sao chép')").addClass('hidden');
                }, 400)
                setTimeout(function () {
                    $(".o_cp_sidebar li:contains('Tạo Hoá Đơn')").addClass('hidden');
                }, 400)
                setTimeout(function () {
                    $(".o_cp_sidebar li:contains('Cập Nhật Hoá Đơn')").addClass('hidden');
                }, 400)
                setTimeout(function () {
                    $(".o_cp_sidebar li:contains('Tạo Giao Hàng')").addClass('hidden');
                }, 400)
                setTimeout(function () {
                    $(".o_cp_sidebar li:contains('Cập Nhật Mới Hoá Đơn')").addClass('hidden');
                }, 400)
                setTimeout(function () {
                    $(".o_cp_sidebar li:contains('Huỷ kiểm tra')").addClass('hidden');
                }, 400)
            }
        },
    });
});