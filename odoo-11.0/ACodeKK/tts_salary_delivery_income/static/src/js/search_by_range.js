odoo.define('tts_salary_delivery_income.tree', function (require) {
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

    ListView.include({

        render_buttons: function ($node) {
            var self = this;
            $('.cl_search_by_range').addClass('hidden')
            this._super.apply(this, arguments);
            var l10n = _t.database.parameters;
            if (self.model == 'salary.delivery.income') {
                self.button_export = $(QWeb.render('salary_delivery_export_button', {}));
                self.button_export.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/export_overview_salary_delivery',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_buttons_print_salary_delivery').length == 0) {
                    self.$buttons.append(self.button_export);
                }
            }
            if (self.model == 'salary.delivery.income') {
                setTimeout(function () {
                   $('.sky-search').addClass('hidden')
                }, 1000)

                sky_fields = [];
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.name === "thang") {
                        sky_fields.push([value.name, value.string]);
                    }
                });

                setTimeout(function () {
                    var current_month = self.$search_thang_nam.find('.salary_delivery');
                    var today = new Date();
                    var mm = String(today.getMonth() + 1).padStart(2, '0')

                    today = mm

                    current_month.val(today)

                    current_month.trigger('change');
                }, 1000);

                if (sky_fields.length > 0) {
                    self.$search_thang_nam = $(QWeb.render('SearchThangNam', {'sky_fields': sky_fields}))
                    self.$search_thang_nam.find('.salary_delivery').on('change', function () {
                        self.search_thangnam();
                    });

                    if ($('.cl_show_credit_debit').length > 0) {
                        setTimeout(function () {
                            self.$search_thang_nam.appendTo($('.cl_show_credit_debit'));
                        }, 1500);
                    } else {
                        setTimeout(function () {
                            self.$search_thang_nam.appendTo($('.cl_show_credit_debit'));
                        }, 1500);
                    }
                }
            }
        },

        search_thangnam: function () {
            var self = this;
            var domain = self.dataset.domain;
            if (self.$search_thang_nam) {
                var state = self.$search_thang_nam.find('.salary_delivery').val()
                var date = new Date()
                var year = date.getFullYear();
                if (state) {
                    try {
                        for( var i=domain.length - 1; i>=0; i--){
                            if(domain[i] && (domain[i][0] === 'thang')) {
                                domain.splice(i, 1);
                            }
                        }
                    }
                    catch (e) {
                        console.error(e);
                    }
                    if (state != 'all') {
                        domain.push(['thang', '=', state], ['nam', '=', year]);
                    }
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
        },
    });
});