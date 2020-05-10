odoo.define('tree_menu.tree_view_button', function (require) {

    var core = require('web.core');
    var ListView = require('web.ListView');
    var QWeb = core.qweb;
    var session = require('web.session');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var time = require('web.time');
    var data = require('web.data');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var _t = core._t;
    var _lt = core._lt;

    ListView.include({

        render_buttons: function ($node) {
            var self = this;
            this._super($node);

            if (self.model == 'product.interest') {

                self.button_product_interest = $(QWeb.render('product_interest_print', {}));
                self.button_product_interest.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_product_interest_excel',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.$buttons.append(self.button_product_interest)


                setTimeout(function () {
                   $('.sky-search').addClass('hidden')
                }, 1200)

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
                        self.product_interest_search();
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
                        }, 1500);
                    } else {
                        setTimeout(function () {
                            self.$search_state_tthd.appendTo($('.cl_show_credit_debit'));
                        }, 1200);
                        setTimeout(function () {
                            self.$search_product.appendTo($('.cl_show_credit_debit'));
                        }, 1200);
                        setTimeout(function () {
                            self.$clear_all_product.appendTo($('.cl_show_credit_debit'));
                        }, 1500);
                    }
                }
            }
        },

        product_interest_search: function () {
            var self = this;
            var product_name = self.$search_product.find('.search_product_name').val();
            var domain = []
            if (product_name) {
                new Model('product.interest').call('get_product_interest_search', [product_name]).then(function (product_ids) {
                    domain.push(['id', 'in', product_ids]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                });
            }
        },
    });

});