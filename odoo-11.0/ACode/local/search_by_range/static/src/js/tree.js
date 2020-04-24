function sbr_autocomplete(inp, arr) {
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  var currentFocus;
  /*execute a function when someone writes in the text field:*/
  inp.addEventListener("input", function(e) {
      var a, b, i, val = this.value;
      /*close any already open lists of autocompleted values*/
      sbr_closeAllLists();
      if (!val) { return false;}
      currentFocus = -1;
      /*create a DIV element that will contain the items (values):*/
      a = document.createElement("DIV");
      a.setAttribute("id", this.id + "autocomplete-list");
      a.setAttribute("class", "autocomplete-items");
      /*append the DIV element as a child of the autocomplete container:*/
      this.parentNode.appendChild(a);
      /*for each item in the array...*/
      for (i = 0; i < arr.length; i++) {
        /*check if the item starts with the same letters as the text field value:*/
        if ( arr[i] && arr[i].toUpperCase().search(val.toUpperCase()) != -1) {
          /*create a DIV element for each matching element:*/
          b = document.createElement("DIV");
          /*make the matching letters bold:*/
          b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
          b.innerHTML += arr[i].substr(val.length);
          /*insert a input field that will hold the current array item's value:*/
          b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
          /*execute a function when someone clicks on the item value (DIV element):*/
          b.addEventListener("click", function(e) {
              /*insert the value for the autocomplete text field:*/
              inp.value = this.getElementsByTagName("input")[0].value;
              /*close the list of autocompleted values,
              (or any other open lists of autocompleted values:*/
              sbr_closeAllLists();
              $('.sky_customer_name').trigger('change')
              $('.tts_categ_name').trigger('change',['event_trigger'])
              $('.input_source_location_name').trigger('change',['event_trigger'])
              $('.tts_dest_location_name').trigger('change',['event_trigger'])
              $('.search_product_name').trigger('change',['event_trigger'])
              $('.search_city').trigger('change',['event_trigger'])

          });
          a.appendChild(b);
        }
      }
  });
  /*execute a function presses a key on the keyboard:*/
  inp.addEventListener("keydown", function(e) {
      var x = document.getElementById(this.id + "autocomplete-list");
      if (x) x = x.getElementsByTagName("div");
      if (e.keyCode == 40) {
        /*If the arrow DOWN key is pressed,
        increase the currentFocus variable:*/
        currentFocus++;
        /*and and make the current item more visible:*/
        sbr_addActive(x);
      } else if (e.keyCode == 38) { //up
        /*If the arrow UP key is pressed,
        decrease the currentFocus variable:*/
        currentFocus--;
        /*and and make the current item more visible:*/
        sbr_addActive(x);
      } else if (e.keyCode == 13) {
        /*If the ENTER key is pressed, prevent the form from being submitted,*/
        e.preventDefault();
        if (currentFocus > -1) {
          /*and simulate a click on the "active" item:*/
          if (x) x[currentFocus].click();
        }
      }
  });
  function sbr_addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    sbr_removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
  }
  function sbr_removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }
  function sbr_closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }
  /*execute a function when someone clicks in the document:*/
  document.addEventListener("onChange", function (e) {
      sbr_closeAllLists(e.target);

  });
}

/*initiate the autocomplete function on the "myInput" element, and pass along the countries array as possible autocomplete values:*/
// sbr_autocomplete(document.getElementById("input_customer_name"), countries);

odoo.define('search_by_date_range.tree', function (require) {
    "use strict";

    var time         = require('web.time');
    var core         = require('web.core');
    var data         = require('web.data');
    var session      = require('web.session');
    var utils        = require('web.utils');
    var Model        = require('web.Model');
    var ListView     = require('web.ListView');
    var datepicker   = require('web.datepicker');
    var ViewManager  = require('web.ViewManager')
    var _t           = core._t;
    // var _lt         = core._lt;
    var QWeb         = core.qweb;
    var FormView     = require('web.FormView');
    var KanbanRecord = require('web_kanban.Record');

    KanbanRecord.include({
        renderElement: function () {
            this._super();
            var self = this;
            if (self.model == 'stock.picking.type'
                || self.model == 'crm.team'
                || self.model == 'account.journal'
                || self.model == 'ir.module.module') {
                $('.cl_search_by_range').addClass('hidden')
                $('.cl_show_credit_debit').addClass('hidden')
            } else {
                console.log('self.model', self.mode);
            }
        },
    });

    FormView.include({
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);
            $('.cl_search_by_range').addClass('hidden')
            $('.cl_show_credit_debit').addClass('hidden')
        },
    });

    ListView.include({
        init: function (parent, dataset, view_id, options) {
            this._super.apply(this, arguments);
            this.ts_context   = dataset.context.tree_search;
            this.fields_range = dataset.context.fields_range;
            this.ts_fields    = [];
        },

        load_list: function () {
            var self   = this;
            var result = self._super();
            if (self.last_domain) {
                if ($('.cl_search_by_range').hasClass('hidden') && $('.cl_search_by_range').length != 0 && $('.cl_search_by_range')[0].children.length == 0 ) {
                    self.render_buttons()
                  }
                $('.cl_search_by_range').removeClass('hidden')
                $('.cl_show_credit_debit').removeClass('hidden')
            }
            else {
                $('.cl_search_by_range').addClass('hidden')
                $('.cl_show_credit_debit').addClass('hidden')
            }
            this.$('tfoot').css('display', 'table-header-group');
            return result;
        },

        on_button_click: function (event) {
            var self = this;
            var $target = $(event.target),
                field,
                key,
                first_item;

            field = $target.parent().data('field');
            key   = $target.parent().data('key');

            if (field == -1) {
                first_item = $target.parent().parent().children('.tgl_first_item.selected');
                if (!first_item.length) {
                    $target.parent().parent().children('li').removeClass('selected')
                }
            } else {
                first_item = $target.parent().parent().children('.tgl_first_item').removeClass('selected');
            }

            $target.parent().toggleClass('selected');
            this.tgl_search()
            event.stopPropagation();
        },

        render_buttons: function ($node) {
            var self = this;

            this._super.apply(this, arguments);
            var l10n = _t.database.parameters;
            var datepickers_options = {
                pickTime: false,
                startDate: moment({y: 1900}),
                endDate: moment().add(200, "y"),
                calendarWeeks: true,
                icons: {
                    time: 'fa fa-clock-o',
                    date: 'fa fa-calendar',
                    up: 'fa fa-chevron-up',
                    down: 'fa fa-chevron-down'
                },
                language: moment.locale(),
                format: time.strftime_to_moment_format(l10n.date_format),
            }
            if (this.dataset.child_name && this.dataset.child_name != null ) return false;
            self.$buttons.find('.sky-search').remove();
            $('.cl_search_by_range').html('')
            $('.cl_show_credit_debit').html('')

            var sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.store && value.type === 'datetime' || value.type === 'date') {
                    sky_fields.push([value.name, value.string]);
                }
            });
            if (sky_fields.length > 0) {
                self.$search_button = $(QWeb.render('SkyERP.buttons', {'sky_fields': sky_fields}))
                self.$search_button.find('.sky_start_date').datetimepicker(datepickers_options);
                self.$search_button.find('.sky_end_date').datetimepicker(datepickers_options);

                self.$search_button.find('.sky_start_date').on('change', function () {
                    self.tgl_search();
                });
                self.$search_button.find('.sky_end_date').on('change', function () {
                    self.tgl_search();
                });
                self.$search_button.find('.sky_select_field').on('change', function () {
                    self.tgl_search();
                });
                self.$search_button.find('.sky_customer_name').on('change', function () {
                    self.tgl_search();
                });
                if ($('.cl_search_by_range').length > 0) {
                    self.$search_button.appendTo($('.cl_search_by_range'));
                } else {
                    setTimeout(function () {
                        self.$search_button.appendTo($('.cl_search_by_range'));
                        $('.cl_search_by_range').removeClass('hidden')
                    }, 1000);
                }
            }

            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.string && value.string.length > 1
                    && value.store && value.type === "many2one"
                    && (value.name === "partner_id" || value.name === "order_partner_id")) {
                    sky_fields.push([value.name, value.string]);
                }
            });

            if (sky_fields.length > 0) {
                self.$search_customer = $(QWeb.render('SkyERP.SearchCustomer', {'sky_fields': sky_fields}))
                self.$search_customer.find('.sky_customer_name').on('change', function () {
                    self.tgl_search();
                });
                // self.$search_customer.appendChild(document.createElement('div'))
                // self.$search_customer.appendTo($('.cl_search_by_range'));
                if ($('.cl_search_by_range').length > 0) {
                    self.$search_customer.appendTo($('.cl_search_by_range'));
                } else {
                    setTimeout(function () {
                        self.$search_customer.appendTo($('.cl_search_by_range'));
                    }, 1000);
                }
                new Model("res.partner").call("get_customer_list", [self.fields_view.model]).then(function (customer_ids) {
                        sbr_autocomplete(self.$search_customer.find('#input_customer_name')[0], customer_ids);
                    });
            }

            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.string && value.string.length > 1 && value.store && value.name === "number_origin") {
                    sky_fields.push([value.name, value.string]);
                }
            });

            if (sky_fields.length <= 0) {
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.store && value.name === "origin" || value.name === "note" || value.name === "notes" ) {
                        sky_fields.push([value.name, value.string]);
                    }
                });
            }

            if (sky_fields.length > 0 && (self.model == 'stock.picking' || self.model == 'account.invoice' || self.model == 'sale.order' || self.model == 'purchase.order')) {
                self.$search_origin = $(QWeb.render('SkyERP.SearchOrigin', {'sky_fields': sky_fields}))
                self.$search_origin.find('.sky_origin_text').on('change', function () {
                    self.tgl_search();
                });
                // self.$search_customer.appendTo($('.cl_search_by_range'));
                if ($('.cl_search_by_range').length > 0) {
                    self.$search_origin.appendTo($('.cl_search_by_range'));
                } else {
                    setTimeout(function () {
                        self.$search_origin.appendTo($('.cl_search_by_range'));
                    }, 1000);
                }
            }

            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.string && value.string.length > 1 && value.store && (value.type === "integer" || value.type === "float" || value.type === "monetary")) {
                    sky_fields.push([value.name, value.string]);
                }
            });

            if (sky_fields.length == 0) {
                if (self.fields_range) {
                    sky_fields = self.fields_range;
                }
            }

            if (sky_fields.length > 0) {
                self.$search_range = $(QWeb.render('SkyERP.SearchRange', {'sky_fields': sky_fields}))
                // self.$search_range.find('.sky_search_date_range').click(function() {
                //     self.tgl_search();
                // });
                self.$search_range.find('.sky_select_range_field').on('change', function () {
                    self.tgl_search();
                });
                self.$search_range.find('.sky_start_range').on('change', function () {
                    self.tgl_search();
                });
                self.$search_range.find('.sky_end_range').on('change', function () {
                    self.tgl_search();
                });
                // self.$search_range.appendTo($('.cl_search_by_range'));
                if ($('.cl_search_by_range').length > 0) {
                    self.$search_range.appendTo($('.cl_search_by_range'));
                } else {
                    setTimeout(function () {
                        self.$search_range.appendTo($('.cl_search_by_range'));
                    }, 1000);
                }
            }

            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.string && value.string.length > 1 && value.store && value.name === "number_voucher") {
                    sky_fields.push([value.name, value.string]);
                }
            });

            if (sky_fields.length > 0 && self.model == 'account.voucher') {
                self.$search_number_vourcher = $(QWeb.render('SkyERP.SearchNumberVourcher', {'sky_fields': sky_fields}))
                self.$search_number_vourcher.find('.sky_number_vourcher').on('change', function () {
                    self.tgl_search();
                });
                // self.$search_customer.appendTo($('.cl_search_by_range'));
                if ($('.cl_search_by_range').length > 0) {
                    self.$search_number_vourcher.appendTo($('.cl_search_by_range'));
                } else {
                    setTimeout(function () {
                        self.$search_number_vourcher.appendTo($('.cl_search_by_range'));
                    }, 1000);
                }
            }

            if (self.$search_range || self.$search_button || self.$search_origin || self.$search_customer) {
                self.$clear_all = $(QWeb.render('SkyERP.ClearAll', {}))
                $('.cl_search_by_range').on('click', '.button_clear_all', function () {
                    self.clear_tgl_search();
                });
                if ($('.cl_search_by_range').length > 0) {
                    setTimeout(function () {
                        self.$clear_all.appendTo($('.cl_search_by_range'));
                    }, 1000);
                } else {
                    setTimeout(function () {
                        self.$clear_all.appendTo($('.cl_search_by_range'));
                        $('.cl_search_by_range').on('click', '.button_clear_all', function () {
                            self.clear_tgl_search();
                        });
                    }, 1000);
                }
            }

            // Dropdown list cho phep chon nhieu
            _.each(this.ts_context, function (item) {
                var field = _.find(self.columns, function (column) {
                    return column.type == 'many2one' && column.relation && column.name === item.name;
                });
                if (field) {
                    self.ts_fields.push(item.name);
                    new Model(field.relation).query(['id', 'display_name']).filter(new data.CompoundDomain(item.domain, field.domain)).context(new data.CompoundContext()).all().then(function (result) {
                        if (!$('.after_control_panel').length) {
                            var multi_search = $(QWeb.render("TGL.TreeSearch.Item", {
                                'widget': {
                                    'string': item.string,
                                    'key': item.name,
                                    'class_name': 'sky_multi_item_' + item.name,
                                    'fields': result,
                                }
                            }))

                            multi_search.find('li').click(self.on_button_click.bind(self));
                            multi_search.appendTo(self.$buttons);
                        }
                    });
                }
            });
        },

        do_search: function (domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            this.tgl_search()
        },

        clear_tgl_search: function () {
            try {
                var self = this;
                var compound_domain = new data.CompoundDomain(self.last_domain, []);
                self.dataset.domain = compound_domain.eval();
                console.log("clear ----")
                return self.old_search(compound_domain, self.last_context, self.last_group_by);
            } catch (err) {
            }
        },

        tgl_search: function () {

            console.log('1');
            var self = this;
            var domain = [], value, value_tmp;

            _.each(self.ts_fields, function (field) {
                value = $('.sky_item_' + field).val();

                var select_fields = $('.sky_multi_item_' + field).children('.selected'),
                    select_value = [];
                if (select_fields.length > 0) {
                    _.each(select_fields, function (item) {
                        value_tmp = $(item).data('field');
                        if (value_tmp > 0) {
                            select_value.push($(item).data('field'));
                        }
                    });
                    if (select_value.length) {
                        domain.push([field, 'in', select_value]);
                    }

                }
            });

            if (self.$search_button) {
                var start_date = self.$search_button.find('.sky_start_date').val(),
                    end_date = self.$search_button.find('.sky_end_date').val(),
                    field = self.$search_button.find('.sky_select_field').val();

                var l10n = _t.database.parameters;
                var check2 = true;
                if (start_date || end_date) {
                    var check2 = false;
                  new Model("res.partner").call("check_date_type", [field, self.model]).then(function (type) {
                    if (type == 'datetime') {
                      if (start_date) {
                        var start_date_list = start_date.split('/');
                        var mydate = new Date(start_date_list[2] + "/" + start_date_list[1] + "/" + start_date_list[0]);
                        var copiedDate = mydate.setHours(mydate.getHours() - 7);
                        copiedDate = moment(copiedDate).format('YYYY-MM-DD HH:mm:SS');
                        domain.push([field, '>=', copiedDate]);
                      }
                      if (end_date) {
                        console.log('end_date');
                        end_date = moment(moment(end_date, time.strftime_to_moment_format(l10n.date_format + ' ' + l10n.time_format))).format('YYYY-MM-DD 16:59:59');
                        domain.push([field, '<=', end_date]);
                      }
                    }
                    if (type == 'date') {
                      if (start_date) {
                        start_date = moment(moment(start_date, time.strftime_to_moment_format(l10n.date_format))).format('YYYY-MM-DD');
                        domain.push([field, '>=', start_date]);
                      }
                      if (end_date) {
                        end_date = moment(moment(end_date, time.strftime_to_moment_format(l10n.date_format))).format('YYYY-MM-DD');
                        domain.push([field, '<=', end_date]);
                      }
                    }
                    console.log('typeof(self.old_search)', typeof(self.old_search));
                    if (typeof(self.old_search) != 'undefined') {
                        var compound_domain = new data.CompoundDomain(self.last_domain || [], domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    }
                  });
                }
                if (check2 && !self.$search_customer) {
                    console.log('typeof(self.old_search)', typeof(self.old_search));
                    if (typeof(self.old_search) != 'undefined') {
                        var compound_domain = new data.CompoundDomain(self.last_domain || [], domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    }
                }
            }

            if (self.$search_range) {
                var start_range = self.$search_range.find('.sky_start_range').val(),
                    end_range = self.$search_range.find('.sky_end_range').val(),
                    range_field = self.$search_range.find('.sky_select_range_field').val();

                if (start_range) {
                    domain.push([range_field, '>=', parseInt(start_range)]);
                }
                if (end_range) {
                    domain.push([range_field, '<=', parseInt(end_range)]);
                }
            }

            if (self.$search_number_vourcher) {
                var number_voucher = self.$search_number_vourcher.find('.sky_number_vourcher').val(),
                    select_number_vourcher = self.$search_number_vourcher.find('.sky_select_number_vourcher').val()
                if (number_voucher) {
                    domain.push([select_number_vourcher, '=', number_voucher]);
                }
            }

            if (self.$search_origin) {
                var check1 = true;
                var origin_text = self.$search_origin.find('.sky_origin_text').val(),
                    origin_field = self.$search_origin.find('.sky_select_origin_field').val();
                if (origin_text) {
                    check = false;
                    new Model('res.partner').call('get_origin_text_search', [origin_text, origin_field, self.model]).then(function (record_ids) {
                        domain.push(['id', 'in', record_ids]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }

                if (check1 && !self.$search_customer) {
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }

            var check = true;
            if (self.$search_customer) {
                var customer_name = self.$search_customer.find('.sky_customer_name').val(),
                    customer_field = self.$search_customer.find('.sky_select_customer_field').val();
                if (customer_name) {
                    check = false;
                    new Model('res.partner').call('get_customer_name_search', [customer_name]).then(function (partner_ids) {
                        domain.push([customer_field, 'in', partner_ids]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }
            }

            if (check) {
                console.log('typeof(self.old_search)', typeof(self.old_search));
                if (typeof(self.old_search) != 'undefined') {
                    var compound_domain = new data.CompoundDomain(self.last_domain || [], domain);
                    console.log('self.last_domain', self.last_domain, 'domain', domain);
                    self.dataset.domain = compound_domain.eval();
                    console.log('compound_domain.eval()', compound_domain.eval());
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
        },

    });

    return ListView;
});