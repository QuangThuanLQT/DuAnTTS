odoo.define('prinizi_sale_customer_product_purchase.tree', function (require) {
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

        render_buttons: function ($node) {
            var self = this;
            $('.cl_search_by_range').addClass('hidden')
            this._super.apply(this, arguments);
            var l10n = _t.database.parameters;
            if (self.model == 'product.purchase' && self.ViewManager.action.xml_id == 'prinizi_sale_customer_product_purchase.res_product_purchase_action') {
                self.button_export = $(QWeb.render('product_purchase_export_button', {}));
                self.button_export.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/export_overview_product_purchase',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_buttons_print_product_purchase').length == 0) {
                    self.$buttons.append(self.button_export);
                }
            }
            if (self.model == 'product.purchase') {
                setTimeout(function () {
                   $('.sky-search').addClass('hidden')
                }, 1000)

                sky_fields = [];
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.name === "trang_thai_hd") {
                        sky_fields.push([value.name, value.string]);
                    }
                });
                if (sky_fields.length > 0) {
                    self.$search_state_tthd = $(QWeb.render('SearchTrangThaihd', {'sky_fields': sky_fields}))
                    self.$search_state_tthd.find('.product_trang_thai_dh').on('change', function () {
                        self.tgl_search();
                    });
                    self.$search_product = $(QWeb.render('SearchProductSoldWell', {}));
                    self.$clear_all_product = $(QWeb.render('SkyERP.ClearAll', {}))
                    self.$search_product.find('.search_product_name').on('change', function () {
                        self.product_purchase_search();
                    });
                    $('.cl_show_credit_debit').on('click', '.button_clear_all', function () {
                        self.clear_tgl_search();
                    });
                    if ($('.cl_show_credit_debit').length > 0) {
                        setTimeout(function () {
                            self.$search_state_tthd.appendTo($('.cl_show_credit_debit'));
                        }, 1200);
                        setTimeout(function () {
                            self.$search_product.appendTo($('.cl_show_credit_debit'));
                        }, 1200);
                        setTimeout(function () {
                            self.$clear_all_product.appendTo($('.cl_show_credit_debit'));
                        }, 1200);
                    } else {
                        setTimeout(function () {
                            self.$search_state_tthd.appendTo($('.cl_show_credit_debit'));
                        }, 1200);
                        setTimeout(function () {
                            self.$search_product.appendTo($('.cl_show_credit_debit'));
                        }, 1200);
                        setTimeout(function () {
                            self.$clear_all_product.appendTo($('.cl_show_credit_debit'));
                        }, 1200);
                    }
                }
            }
        },

        tgl_search: function () {
            var self = this;
            var domain = self.dataset.domain;
            if (self.$search_state_tthd) {
                var state = self.$search_state_tthd.find('.product_trang_thai_dh').val()
                if (state) {
                    try {
                        for( var i=domain.length - 1; i>=0; i--){
                            if(domain[i] && (domain[i][0] === 'trang_thai_hd')) {
                                domain.splice(i, 1);
                            }
                        }
                    }
                    catch (e) {
                        console.error(e);
                    }
                    if (state != 'all') {
                        domain.push(['trang_thai_hd', '=', state]);
                    }
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
            this._super.apply(this, arguments);
        },
        product_purchase_search: function () {
            var self = this;
            var product_name = self.$search_product.find('.search_product_name').val();
            var domain = []
            if (product_name) {
                new Model('product.purchase').call('get_product_purchase_search', [product_name]).then(function (product_ids) {
                    domain.push(['id', 'in', product_ids]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                });
            }
        },
    });
});