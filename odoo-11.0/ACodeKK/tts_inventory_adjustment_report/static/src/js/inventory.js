odoo.define('tts_inventory_adjustment_report.form', function (require) {
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

    FormView.include({
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);

            if (self.model == 'bao.cao.kiem.kho') {
                setTimeout(function () {
                    $('div.button_hidden_table1').before("<button class='button_hidden_table1 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table1').click(function () {
                        if ($('div.button_hidden_table1').hasClass('hidden')) {
                            $('div.button_hidden_table1').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table1').addClass('hidden')
                        }
                    });

                    $('div.button_hidden_table2').before("<button class='button_hidden_table2 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table2').click(function () {
                        if ($('div.button_hidden_table2').hasClass('hidden')) {
                            $('div.button_hidden_table2').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table2').addClass('hidden')
                        }
                    });

                    $('div.button_hidden_table3').before("<button class='button_hidden_table3 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table3').click(function () {
                        if ($('div.button_hidden_table3').hasClass('hidden')) {
                            $('div.button_hidden_table3').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table3').addClass('hidden')
                        }
                    });

                    $('div.button_hidden_table4').before("<button class='button_hidden_table4 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table4').click(function () {
                        if ($('div.button_hidden_table4').hasClass('hidden')) {
                            $('div.button_hidden_table4').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table4').addClass('hidden')
                        }
                    });

                    $('div.button_hidden_table5').before("<button class='button_hidden_table5 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table5').click(function () {
                        if ($('div.button_hidden_table5').hasClass('hidden')) {
                            $('div.button_hidden_table5').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table5').addClass('hidden')
                        }
                    });

                    $('div.button_hidden_table6').before("<button class='button_hidden_table6 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table6').click(function () {
                        if ($('div.button_hidden_table6').hasClass('hidden')) {
                            $('div.button_hidden_table6').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table6').addClass('hidden')
                        }
                    });

                    $('div.button_hidden_table7').before("<button class='button_hidden_table7 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table7').click(function () {
                        if ($('div.button_hidden_table7').hasClass('hidden')) {
                            $('div.button_hidden_table7').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table7').addClass('hidden')
                        }
                    });

                    $('div.button_hidden_table8').before("<button class='button_hidden_table8 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table8').click(function () {
                        if ($('div.button_hidden_table8').hasClass('hidden')) {
                            $('div.button_hidden_table8').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table8').addClass('hidden')
                        }
                    });

                    $('div.button_hidden_table9').before("<button class='button_hidden_table9 fa fa-sort-desc pull-right'></button>")
                    $('button.button_hidden_table9').click(function () {
                        if ($('div.button_hidden_table9').hasClass('hidden')) {
                            $('div.button_hidden_table9').removeClass('hidden')
                        } else {
                            $('div.button_hidden_table9').addClass('hidden')
                        }
                    });
                }, 400);
            }
        }
    });


});