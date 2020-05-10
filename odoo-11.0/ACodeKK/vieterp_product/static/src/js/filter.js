function pr_sbr_autocomplete(inp, arr) {
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
              $('.categ_name').trigger('change',['event_trigger'])

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
        increase the currentFocus var   iable:*/
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

odoo.define('vieterp_product.product_tree', function (require) {
    "use strict";

    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var _t = core._t;
    var QWeb = core.qweb;
    var FormView = require('web.FormView');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');

    FormView.include({
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);
            $('.pr_search_by_range').addClass('hidden')
        },
    });

    ListView.include({

        load_list: function () {
            var self   = this;
            var result = self._super();
            if (self.last_domain) {
                if ($('.pr_search_by_range').hasClass('hidden') && $('.pr_search_by_range').length != 0 && $('.pr_search_by_range')[0].children.length == 0 ) {
                    self.render_buttons()
                }
                $('.pr_search_by_range').removeClass('hidden')
            }
            else {
                $('.pr_search_by_range').addClass('hidden')
            }
            this.$('tfoot').css('display', 'table-header-group');
            return result;
        },

        do_search: function (domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            this.tgl_search()
            if (self.model == 'product.product' && self.$product_search_categ) {
                this.product_search_function();
            }
        },

        tgl_search: function() {
            var self = this;
            var domain = [];
            var compound_domain = new data.CompoundDomain(self.last_domain, domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        },

        render_buttons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            $('.pr_search_by_range').html('')

            if (self.model == 'product.product') {
                self.$product_print = $(QWeb.render('buttons_print_excel', {}));

                self.$product_print.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_product_excel',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_picking_export_overview').length == 0) {
                        self.$buttons.append(self.$product_print)
                    }

                self.$product_search_categ = $(QWeb.render('SearchProductCateg', {}));
                self.$product_search_categ.find('.categ_name').on('change', function () {
                    self.product_search_function();
                });
                if ($('.pr_search_by_range').length > 0) {
                    setTimeout(function () {
                        $('.pr_search_by_range').removeClass('hidden')
                        self.$product_search_categ.appendTo($('.pr_search_by_range'));
                    }, 400);
                } else {
                    setTimeout(function () {
                        $('.pr_search_by_range').removeClass('hidden')
                        self.$product_search_categ.appendTo($('.pr_search_by_range'));
                    }, 400)
                }

                new Model("product.product").call("get_categ_list", []).then(function (categ_ids) {
                    pr_sbr_autocomplete(self.$product_search_categ.find('#input_categ_name')[0], categ_ids);
                });
            }
        },

        product_search_function: function () {
            var self = this;
            var categ_name = self.$product_search_categ.find('.categ_name').val();
            var domain = []
            if (categ_name) {
                new Model('product.product').call('get_categ_name_search', [categ_name]).then(function (product_ids) {
                    domain.push(['id', 'in', product_ids]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                });
            }
            else {
                try {
                    var self = this;
                    var compound_domain = new data.CompoundDomain(self.last_domain, []);
                    self.dataset.domain = compound_domain.eval();
                    console.log("clear ----")
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                } catch (err) {
                }
            }
        }
    });
});