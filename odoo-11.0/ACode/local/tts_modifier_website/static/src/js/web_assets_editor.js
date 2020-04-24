odoo.define('tts_modifier_website.website_sale', function (require) {
    "use strict";

    var base = require('web_editor.base');
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    var _t = core._t;
    var Model = require('web.Model');
    // required('website_sale.website_sale')

    var dropdown = document.getElementsByClassName("dropdown-btn");
    var i;
    for (i = 0; i < dropdown.length; i++) {
        dropdown[i].addEventListener("click", function () {
            this.classList.toggle("active");
            var dropdownContent = this.nextElementSibling;
            if (dropdownContent.style.display == "none") {
                dropdownContent.style.display = "";
            }
            else {
                dropdownContent.style.display = "none";
            }
        });
    }
    $(".toggle-password").click(function () {

        $(this).toggleClass("fa-eye fa-eye-slash");
        var input = $($(this).attr("toggle"));
        if (input.attr("type") == "password") {
            input.attr("type", "text");
        } else {
            input.attr("type", "password");
        }
    });

    $(function () {

        if (localStorage.chkbx && localStorage.chkbx != '') {
            $('#remember_me').attr('checked', 'checked');
            $('#login').val(localStorage.login);
            $('#password').val(localStorage.password);
        } else {
            $('#remember_me').removeAttr('checked');
            $('#login').val('');
            $('#password').val('');
        }

        $('#remember_me').click(function () {

            if ($('#remember_me').is(':checked')) {

                localStorage.login = $('#login').val();
                localStorage.password = $('#password').val();
                localStorage.chkbx = $('#remember_me').val();
            } else {
                localStorage.login = '';
                localStorage.password = '';
                localStorage.chkbx = '';
            }
        });
    });

    $('.oe_website_sale #wk_loader').click(function () {
        var count = 2;
        var page = $("#products_grid table tbody td").length / 50
        var ppg = 18;
        var offset = 0;
        count = parseInt(count);
        if (page < 1 && page > 0) {
            page = 1
        }
        page = parseInt(page + 1);
        offset = parseInt(offset);
        if (page != 0) {
            try {
                var category = $('html').data('main-object')
                offset = ppg;
                ppg = ppg + 8;
                var view = 'grid';
                $("div#wk_loader").addClass('show');
                if ($('.oe_list').length) {
                    view = 'list';
                }
                ajax.jsonRpc("/lazy/load", 'call', {
                    'page': page,
                    'offset': offset,
                    'view': view,
                    'category': category,
                }).then(function (data) {
                    if (data) {
                        $("div#wk_loader").hide();
                        var path = window.location.pathname;
                        if (view == 'list') {
                            $("#products_grid div.oe_list:last").after(data.data_grid);
                        } else {
                            var new_tr = $("#products_grid table tr:last").after(data.data_grid);
                            $(".button_heart").click(function (event) {
                                var self = this
                                if (self.clicking == false || typeof self.clicking === 'undefined') {
                                    self.clicking = true
                                    setTimeout(function () {
                                        self.clicking = false
                                    }, 2000)
                                    var product = parseInt($(this).attr('data-target'));
                                    if ($(this).hasClass('active')) {
                                        $(this).removeClass('active');
                                        new Model("product.interest").call("change_product_interest_list", [1, product, 'remove'])
                                    } else {
                                        $(this).addClass('active');
                                        new Model("product.interest").call("change_product_interest_list", [1, product, 'add'])
                                    }
                                }
                            });

                            $('.oe_website_sale #products_grid #product_quick_view')
                                .click(_.debounce(function (event) {
                                    var $form = $(this).closest('form');
                                    var product_id = this.dataset.target;
                                    var self = this
                                    event.preventDefault();
                                    if (self.ready_popup == false || typeof self.ready_popup === 'undefined') {
                                        self.ready_popup = true
                                        setTimeout(function () {
                                            self.ready_popup = false
                                        }, 5000)
                                        ajax.jsonRpc("/shop/product_quick_view", 'call', {
                                            'product_id': product_id,
                                        }).then(function (modal) {
                                            var $modal = $(modal);

                                            // $modal.find('img:first').attr("src", "/web/image/product.product/" + product_id + "/image_medium");

                                            // disable opacity on the <form> if currently active (in case the product is
                                            // not published), as it interferes with bs modals
                                            $form.addClass('css_options');

                                            $modal.appendTo($form)
                                                .modal()
                                                .on('hidden.bs.modal', function () {
                                                    $form.removeClass('css_options'); // possibly reactivate opacity (see above)
                                                    $(this).remove();
                                                });

                                            $modal.on('click', '.a-submit', function () {
                                                var $a = $(this);
                                                var product_id = $('.popup_add_to_cart #product_details .js_product_quantity .product_size_id')
                                                var js_quantity = $('.popup_add_to_cart #product_details .js_product_quantity .js_quantity')
                                                var data_list = []
                                                for (var i = 0; i < js_quantity.length; i++) {
                                                    data_list.push({
                                                        'quantity': js_quantity[i].value,
                                                        'product': product_id[i].text,
                                                    })
                                                }
                                                ajax.jsonRpc("/shop/product_popup/update_option", 'call', {'data_list': data_list})
                                                    .then(function (quantity) {
                                                        if (!$a.hasClass('js_goto_shop')) {
                                                            if (quantity.indexOf('modal_optional_products') == -1) {
                                                                window.location.pathname = window.location.pathname.replace(/shop([\/?].*)?$/, "shop/cart");
                                                            }
                                                            else {
                                                                return false;
                                                            }
                                                            // if (quantity === 'warning_error') {
                                                            //     $('.oe_website_sale #add_to_cart').trigger('click');
                                                            // }
                                                            // else {
                                                            //
                                                            // }
                                                        }
                                                        if (quantity != 'warning_error') {
                                                            var $q = $(".my_cart_quantity");
                                                            $q.parent().parent().removeClass("hidden", !quantity);
                                                            $q.html(quantity).hide().fadeIn(600);
                                                        }
                                                    })
                                                $modal.modal('hide');
                                            });

                                            $modal.on('change', 'input.js_product_change', function () {
                                                var self = this;
                                                var $parent = $(this).closest('.js_product');
                                                $.when(base.ready()).then(function () {
                                                    $parent.find(".oe_default_price:first .oe_currency_value").html(price_to_str(+$(self).data('lst_price')));
                                                    $parent.find(".oe_price:first .oe_currency_value").html(price_to_str(+$(self).data('price')));
                                                });
                                            });


                                            $modal.on('click', '.css_attribute_color input', function (event) {
                                                $modal.find('.css_attribute_color').removeClass("active");
                                                $modal.find('.css_attribute_color:has(input:checked)').addClass("active");
                                            });

                                            $('div.js_product', $modal).each(function () {
                                                setTimeout(function () {
                                                    // var js_quantity = $modal.find('.oe_website_sale_modifier #product_details').find('input.js_quantity').first()
                                                    // if (js_quantity.length != 0) {
                                                    //     js_quantity.trigger('change')
                                                    // }
                                                    // else {
                                                    $modal.find('.oe_website_sale_modifier #product_details input.js_quantity').first().trigger('change')
                                                    // }
                                                }, 1);
                                            });

                                            $modal.on('change', 'input.js_quantity, input.js_variant_popup_change, select.js_variant_popup_change, ul[data-attribute_popup_value_ids]', function (ev) {
                                                var $ul = $(ev.target).closest('.js_add_cart_variants');
                                                var $parent = $ul.closest('.js_product');
                                                var $product_id = $parent.find('.product_id').first();
                                                var $price = $parent.find(".oe_price:first .oe_currency_value");
                                                var $default_price = $parent.find(".oe_default_price:first .oe_currency_value");
                                                var $optional_price = $parent.find(".oe_optional:first .oe_currency_value");
                                                var variant_ids = $ul.data("attribute_popup_value_ids");
                                                var values = [];
                                                var unchanged_values = $parent.find('div.oe_unchanged_value_ids').data('unchanged_value_ids') || [];
                                                var js_quantity = $parent.find('table.js_product_size input.js_quantity')
                                                var gia_ban_san_pham = $parent.find('table.js_product_size a.gia_ban_san_pham')
                                                var js_quantity_not_variant = $('table.js_product_not_variant input.js_quantity')
                                                var js_quantity_only_color = $('table.js_product_only_color input.js_quantity')

                                                $parent.find('input.js_variant_popup_change:checked, select.js_variant_popup_change').each(function () {
                                                    values.push(+$(this).val());
                                                });
                                                values = values.concat(unchanged_values);

                                                $parent.find("label").removeClass("text-muted css_not_available");

                                                var product_id = false;
                                                var check_qty = false;
                                                var total_qty = 0
                                                var total_amount = 0
                                                if (js_quantity_only_color.length != 0) {
                                                    var product_size_id_only_color = $('table.js_product_only_color a.product_size_id')[0]
                                                    var gia_ban_san_pham_only_color = $('table.js_product_only_color a.gia_ban_san_pham')[0]
                                                    var sp_co_the_ban = $('table.js_product_only_color a.sp_co_the_ban')[0]
                                                    var css_editable_mode_hidden = $('div.js_product div.css_editable_mode_hidden')
                                                    var values_full = []
                                                    css_editable_mode_hidden.css({'margin-top': '15px'})

                                                    $parent.find('input.js_variant_popup_change:checked, select.js_variant_popup_change').each(function () {
                                                        values_full.push(+$(this).val());
                                                    });
                                                    if (values_full.length == 0) {
                                                        values_full.push(parseInt(variant_ids[0][1]))
                                                    }
                                                    for (var k in variant_ids) {
                                                        if (_.isEmpty(_.difference(variant_ids[k][1], values_full))) {
                                                            product_size_id_only_color.text = parseInt(variant_ids[k][0])
                                                            product_id = variant_ids[k][0];
                                                            gia_ban_san_pham_only_color.text = parseInt(variant_ids[k][2])
                                                            if (parseInt(variant_ids[k][5]) == 1) {
                                                                if (parseInt(variant_ids[k][4]) <= 0) {
                                                                    sp_co_the_ban.style.color = "red"
                                                                    sp_co_the_ban.text = 'Cháy hàng'
                                                                }
                                                                else {
                                                                    sp_co_the_ban.style.color = "green"
                                                                    sp_co_the_ban.text = variant_ids[k][4]
                                                                }
                                                            }
                                                            else {
                                                                if (parseInt(variant_ids[k][5]) == 3) {
                                                                    if (parseInt(variant_ids[k][4]) <= 0) {
                                                                        sp_co_the_ban.style.color = "red"
                                                                        sp_co_the_ban.text = 'Cháy hàng'
                                                                    }
                                                                    else {
                                                                        sp_co_the_ban.style.color = "green"
                                                                        sp_co_the_ban.text = 'Còn hàng'
                                                                    }
                                                                }
                                                                else {
                                                                    if (parseInt(variant_ids[k][4]) <= 0) {
                                                                        sp_co_the_ban.style.color = "red"
                                                                        sp_co_the_ban.text = 'Cháy hàng'
                                                                    }
                                                                    else {
                                                                        if (parseInt(variant_ids[k][4]) < parseInt(variant_ids[k][6])) {
                                                                            sp_co_the_ban.style.color = "green"
                                                                            sp_co_the_ban.text = variant_ids[k][4]
                                                                        }
                                                                        else {
                                                                            sp_co_the_ban.style.color = "green"
                                                                            sp_co_the_ban.text = _.str.sprintf(_t(">%s"), variant_ids[k][6])
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                    total_qty = parseInt(js_quantity_only_color[0].value)
                                                    total_amount = total_qty * parseInt(gia_ban_san_pham_only_color.text)
                                                }
                                                if (js_quantity_not_variant.length != 0) {
                                                    var product_size_id_not_varian = $('table.js_product_not_variant a.product_size_id')[0]
                                                    var gia_ban_san_pham_not_variant = $('table.js_product_not_variant a.gia_ban_san_pham')[0]
                                                    var sp_co_the_ban = $('table.js_product_not_variant a.sp_co_the_ban')[0]
                                                    var css_editable_mode_hidden = $('div.js_product div.css_editable_mode_hidden')
                                                    css_editable_mode_hidden.css({'margin-top': '15px'})

                                                    if (variant_ids) {
                                                        product_size_id_not_varian.text = parseInt(variant_ids[0][0])
                                                        gia_ban_san_pham_not_variant.text = parseInt(variant_ids[0][2])
                                                        if (parseInt(variant_ids[0][5]) == 1) {
                                                            if (parseInt(variant_ids[0][4]) <= 0) {
                                                                sp_co_the_ban.style.color = "red"
                                                                sp_co_the_ban.text = 'Cháy hàng'
                                                            }
                                                            else {
                                                                sp_co_the_ban.style.color = "green"
                                                                sp_co_the_ban.text = variant_ids[0][4]
                                                            }
                                                        }
                                                        else {
                                                            if (parseInt(variant_ids[0][5]) == 3) {
                                                                if (parseInt(variant_ids[0][4]) <= 0) {
                                                                    sp_co_the_ban.style.color = "red"
                                                                    sp_co_the_ban.text = 'Cháy hàng'
                                                                }
                                                                else {
                                                                    sp_co_the_ban.style.color = "green"
                                                                    sp_co_the_ban.text = 'Còn hàng'
                                                                }
                                                            }
                                                            else {
                                                                if (parseInt(variant_ids[0][4]) <= 0) {
                                                                    sp_co_the_ban.style.color = "red"
                                                                    sp_co_the_ban.text = 'Cháy hàng'
                                                                }
                                                                else {
                                                                    if (parseInt(variant_ids[0][4]) < parseInt(variant_ids[0][6])) {
                                                                        sp_co_the_ban.style.color = "green"
                                                                        sp_co_the_ban.text = variant_ids[0][4]
                                                                    }
                                                                    else {
                                                                        sp_co_the_ban.style.color = "green"
                                                                        sp_co_the_ban.text = _.str.sprintf(_t(">%s"), variant_ids[0][6])
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                    total_qty = parseInt(js_quantity_not_variant[0].value)
                                                    total_amount = total_qty * parseInt(gia_ban_san_pham_not_variant.text)
                                                }
                                                if (js_quantity.length != 0) {
                                                    for (var q = 0; q < js_quantity.length; q++) {
                                                        var product_size_id = $parent.find('table.js_product_size a.product_size_id')[q]
                                                        var sp_co_the_ban = $parent.find('table.js_product_size a.sp_co_the_ban')[q]
                                                        var gia_ban_san_pham = $parent.find('table.js_product_size a.gia_ban_san_pham')
                                                        var product_status_qty = $parent.find('table.js_product_size a.product_status_qty')[q]
                                                        var total_amount_product = $parent.find('b.total_amount_product')
                                                        var variant_id = js_quantity[q].name.split('-')[2]
                                                        var values_full = []

                                                        total_qty += parseInt(js_quantity[q].value)
                                                        if (gia_ban_san_pham.length != 0 && gia_ban_san_pham[q].text) {
                                                            total_amount += parseInt(js_quantity[q].value) * parseInt(gia_ban_san_pham[q].text)
                                                        }

                                                        $parent.find('input.js_variant_popup_change:checked, select.js_variant_popup_change').each(function () {
                                                            values_full.push(+$(this).val());
                                                        });
                                                        values_full.push(parseInt(variant_id))
                                                        if (!(js_quantity[q].value && js_quantity[q].value != '' && js_quantity[q].value != 0)) {
                                                            js_quantity[q].value = 0
                                                        }
                                                        else {
                                                            check_qty = true
                                                            // if (total_amount_product.length != 0) {
                                                            //     for (var k in variant_ids) {
                                                            //         if (_.isEmpty(_.difference(variant_ids[k][1], values_full))) {
                                                            //             total_amount_product[0].innerHTML = variant_ids[k][2]
                                                            //         }
                                                            //     }
                                                            // }
                                                        }
                                                        for (var k in variant_ids) {
                                                            if (_.isEmpty(_.difference(variant_ids[k][1], values_full))) {
                                                                if (parseInt(variant_ids[k][5]) == 1) {
                                                                    if (parseInt(variant_ids[k][4]) <= 0) {
                                                                        // sp_co_the_ban.text = '0'
                                                                        product_size_id.text = variant_ids[k][0]
                                                                        sp_co_the_ban.style.color = "red"
                                                                        sp_co_the_ban.text = 'Cháy hàng'
                                                                        if (gia_ban_san_pham.length != 0) {
                                                                            gia_ban_san_pham[q].text = variant_ids[k][2]
                                                                        }
                                                                    }
                                                                    else {
                                                                        sp_co_the_ban.style.color = "green"
                                                                        sp_co_the_ban.text = variant_ids[k][4]
                                                                        product_size_id.text = variant_ids[k][0]
                                                                        // product_status_qty.style.color = "green"
                                                                        // product_status_qty.text = 'Còn hàng'
                                                                        if (gia_ban_san_pham.length != 0) {
                                                                            gia_ban_san_pham[q].text = variant_ids[k][2]
                                                                        }
                                                                    }
                                                                }

                                                                else {
                                                                    if (parseInt(variant_ids[k][5]) == 3) {
                                                                        if (parseInt(variant_ids[k][4]) <= 0) {
                                                                            product_size_id.text = variant_ids[k][0]
                                                                            sp_co_the_ban.style.color = "red"
                                                                            sp_co_the_ban.text = 'Cháy hàng'
                                                                            if (gia_ban_san_pham.length != 0) {
                                                                                gia_ban_san_pham[q].text = variant_ids[k][2]
                                                                            }
                                                                        }
                                                                        else {
                                                                            product_size_id.text = variant_ids[k][0]
                                                                            sp_co_the_ban.style.color = "green"
                                                                            sp_co_the_ban.text = 'Còn hàng'
                                                                            if (gia_ban_san_pham.length != 0) {
                                                                                gia_ban_san_pham[q].text = variant_ids[k][2]
                                                                            }
                                                                        }
                                                                    }
                                                                    else {
                                                                        if (parseInt(variant_ids[k][4]) <= 0) {
                                                                            product_size_id.text = variant_ids[k][0]
                                                                            sp_co_the_ban.style.color = "red"
                                                                            sp_co_the_ban.text = 'Cháy hàng'
                                                                            if (gia_ban_san_pham.length != 0) {
                                                                                gia_ban_san_pham[q].text = variant_ids[k][2]
                                                                            }
                                                                        }
                                                                        else {
                                                                            if (parseInt(variant_ids[k][4]) < parseInt(variant_ids[k][6])) {
                                                                                sp_co_the_ban.style.color = "green"
                                                                                sp_co_the_ban.text = variant_ids[k][4]
                                                                                product_size_id.text = variant_ids[k][0]
                                                                                if (gia_ban_san_pham.length != 0) {
                                                                                    gia_ban_san_pham[q].text = variant_ids[k][2]
                                                                                }
                                                                            }
                                                                            else {
                                                                                sp_co_the_ban.style.color = "green"
                                                                                sp_co_the_ban.text = _.str.sprintf(_t(">%s"), variant_ids[k][6])
                                                                                product_size_id.text = variant_ids[k][0]
                                                                                if (gia_ban_san_pham.length != 0) {
                                                                                    gia_ban_san_pham[q].text = variant_ids[k][2]
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                                break;
                                                            }
                                                        }
                                                        // }
                                                    }
                                                }
                                                var total_qty_html = $('.popup_add_to_cart .total_qty')
                                                var total_price_html = $('.popup_add_to_cart .total_price')
                                                if (total_qty_html.length != 0 && total_price_html.length != 0) {
                                                    total_qty_html.val(total_qty)
                                                    total_price_html.val(String(total_amount) + " đ")
                                                }

                                                else {
                                                    for (var k in variant_ids) {
                                                        if (_.isEmpty(_.difference(variant_ids[k][1], values))) {
                                                            $.when(base.ready()).then(function () {
                                                                $price.html(price_to_str(variant_ids[k][2]));
                                                                $default_price.html(price_to_str(variant_ids[k][3]));
                                                            });
                                                            if (variant_ids[k][3] - variant_ids[k][2] > 0.01) {
                                                                $default_price.closest('.oe_website_sale_modifier').addClass("discount");
                                                                $optional_price.closest('.oe_optional').show().css('text-decoration', 'line-through');
                                                                $default_price.parent().removeClass('hidden');
                                                            } else {
                                                                $optional_price.closest('.oe_optional').hide();
                                                                $default_price.parent().addClass('hidden');
                                                            }
                                                            product_id = variant_ids[k][0];
                                                            break;
                                                        }
                                                    }
                                                }

                                                $parent.find("input.js_variant_popup_change:radio, select.js_variant_popup_change").each(function () {
                                                    var $input = $(this);
                                                    var id = +$input.val();
                                                    var values = [id];

                                                    $parent.find("ul:not(:has(input.js_variant_popup_change[value='" + id + "'])) input.js_variant_popup_change:checked, select.js_variant_popup_change").each(function () {
                                                        values.push(+$(this).val());
                                                    });

                                                    for (var k in variant_ids) {
                                                        if (!_.difference(values, variant_ids[k][1]).length) {
                                                            return;
                                                        }
                                                    }
                                                    $input.closest("label").addClass("css_not_available");
                                                    $input.find("option[value='" + id + "']").addClass("css_not_available");
                                                });

                                                if (product_id || check_qty) {
                                                    $parent.removeClass("css_not_available");
                                                    $parent.find("#add_to_cart").removeClass("disabled");
                                                    if (product_id) {
                                                        $product_id.val(product_id);
                                                    }
                                                    else {
                                                        $product_id.val(0);
                                                    }
                                                } else {
                                                    $parent.addClass("css_not_available");
                                                    $product_id.val(0);
                                                    $parent.find("#add_to_cart").addClass("disabled");
                                                }
                                            });

                                            $modal.on("click", "a.js_add, a.js_remove", function (event) {
                                                event.preventDefault();
                                                var $parent = $(this).parents('.js_product:first');
                                                $parent.find("a.js_add, span.js_remove").toggleClass("hidden");
                                                $parent.find("input.js_optional_same_quantity").val($(this).hasClass("js_add") ? 1 : 0);
                                                $parent.find(".js_remove");
                                            });

                                            $modal.on("change", "input.js_quantity", function () {
                                                var qty = parseFloat($(this).val());
                                                if (qty === 1) {
                                                    $(".js_remove .js_items").addClass("hidden");
                                                    $(".js_remove .js_item").removeClass("hidden");
                                                } else {
                                                    $(".js_remove .js_items").removeClass("hidden").text($(".js_remove .js_items:first").text().replace(/[0-9.,]+/, qty));
                                                    $(".js_remove .js_item").addClass("hidden");
                                                }
                                            });
                                        });
                                        return false;
                                    }
                                }, 200, true));
                        }
                        if (data.count == 0) {
                            $("div#wk_loader a").text("");
                            $("div#wk_loader a").css("background-image", "none");
                            $("div#wk_loader a").css("display", "unset");
                        }
                    }
                }).fail(function (error) {
                });
            } catch (error) {
                console.log("++++++++++++++++++" + error);
            }
        }
    })

    $('.oe_website_sale_modifier #add_to_cart, .oe_website_sale_modifier #products_grid .a-submit')
        .off('click')
        .removeClass('a-submit')
        .click(_.debounce(function (event) {
            var $form = $(this).closest('form');
            var js_product_quantity = $('tr.js_product_quantity')
            var product_id = []
            var quantity = 0
            if (js_product_quantity.length != 0) {
                for (var q = 0; q < js_product_quantity.length; q++) {
                    var js_quantity = $('tr.js_product_quantity input.js_quantity')[q]
                    var product_size_id = $('tr.js_product_quantity a.product_size_id')[q]
                    if (js_quantity.value && js_quantity.value != '' && js_quantity.value != 0) {
                        var quantity_list = [parseInt(js_quantity.value)]
                        quantity_list.push(parseInt(product_size_id.text))
                        product_id.push(quantity_list)
                    }
                }
            }

            event.preventDefault();
            ajax.jsonRpc("/shop/modal", 'call', {
                'product_id': product_id,
                'kwargs': {
                    'context': _.extend({'quantity': quantity}, base.get_context())
                },
            }).then(function (modal) {
                var $modal = $(modal);

                // $modal.find('img:first').attr("src", "/web/image/product.product/" + product_id + "/image_medium");

                // disable opacity on the <form> if currently active (in case the product is
                // not published), as it interferes with bs modals
                $form.addClass('css_options');

                $modal.appendTo($form)
                    .modal()
                    .on('hidden.bs.modal', function () {
                        $form.removeClass('css_options'); // possibly reactivate opacity (see above)
                        $(this).remove();
                    });

                $modal.on('click', '.a-submit', function () {
                    var $a = $(this);
                    $form.ajaxSubmit({
                        url: '/shop/cart/update_option',
                        data: {lang: base.get_context().lang},
                        success: function (quantity) {
                            if (!$a.hasClass('js_goto_shop')) {
                                if (quantity === 'warning_error') {
                                    $('.oe_website_sale_modifier #add_to_cart').trigger('click');
                                }
                                else {
                                    window.location.pathname = window.location.pathname.replace(/shop([\/?].*)?$/, "shop/cart");
                                }
                            }
                            if (quantity != 'warning_error') {
                                var $q = $(".my_cart_quantity");
                                $q.parent().parent().removeClass("hidden", !quantity);
                                $q.html(quantity).hide().fadeIn(600);
                            }
                        }
                    });
                    $modal.modal('hide');
                });

                $modal.on('click', '.css_attribute_color input', function (event) {
                    $modal.find('.css_attribute_color').removeClass("active");
                    $modal.find('.css_attribute_color:has(input:checked)').addClass("active");
                });

                $modal.on("click", "a.js_add, a.js_remove", function (event) {
                    event.preventDefault();
                    var $parent = $(this).parents('.js_product:first');
                    $parent.find("a.js_add, span.js_remove").toggleClass("hidden");
                    $parent.find("input.js_optional_same_quantity").val($(this).hasClass("js_add") ? 1 : 0);
                    $parent.find(".js_remove");
                });

                $modal.on("change", "input.js_quantity", function () {
                    var qty = parseFloat($(this).val());
                    if (qty === 1) {
                        $(".js_remove .js_items").addClass("hidden");
                        $(".js_remove .js_item").removeClass("hidden");
                    } else {
                        $(".js_remove .js_items").removeClass("hidden").text($(".js_remove .js_items:first").text().replace(/[0-9.,]+/, qty));
                        $(".js_remove .js_item").addClass("hidden");
                    }
                });

                $modal.find('input[name="add_qty"]').val(quantity).change();
                $('.js_add_cart_variants').each(function () {
                    $('input.js_variant_change, select.js_variant_change', this).first().trigger('change');
                });

                $modal.on("change", 'input[name="add_qty"]', function (event) {
                    var product_id = $($modal.find('span.oe_price[data-product-id]')).first().data('product-id');
                    var product_ids = [product_id];
                    var $products_dom = [];
                    $("ul.js_add_cart_variants[data-attribute_value_ids]").each(function () {
                        var $el = $(this);
                        $products_dom.push($el);
                        _.each($el.data("attribute_value_ids"), function (values) {
                            product_ids.push(values[0]);
                        });
                    });
                });
            });
            return false;
        }, 200, true));

    if (!$('.oe_website_sale_modifier').length) {
        return $.Deferred().reject("DOM doesn't contain '.oe_website_sale_modifier'");
    }

    $('.oe_website_sale_modifier').each(function () {
        var oe_website_sale_modifier = this;

        $(oe_website_sale_modifier).on("change", 'input[name="add_qty"]', function (event) {
            var product_ids = [];
            var product_dom = $(".js_product .js_add_cart_variants[data-attribute_value_ids]");
            var qty = $(event.target).closest('form').find('input[name="add_qty"]').val();
            if (!product_dom.length) {
                return;
            }
            _.each(product_dom, function (prod) {
                _.each($(prod).data("attribute_value_ids"), function (entry) {
                    if (product_ids.indexOf(entry[0]) === -1) {
                        product_ids.push(entry[0]);
                    }
                });
            });

            if ($("#product_detail").length) {
                // display the reduction from the pricelist in function of the quantity
                ajax.jsonRpc("/shop/get_unit_price", 'call', {'product_ids': product_ids, 'add_qty': parseInt(qty)})
                    .then(function (data) {
                        _.each(product_dom, function (prod) {
                            var current = $(prod).data("attribute_value_ids");
                            for (var j = 0; j < current.length; j++) {
                                current[j][2] = data[current[j][0]];
                            }
                            $(prod).trigger("change");
                        });
                    });
            }
        });

        // change for css
        $(oe_website_sale_modifier).on('mouseup touchend', '.js_publish', function (ev) {
            $(ev.currentTarget).parents(".thumbnail").toggleClass("disabled");
        });

        var clickwatch = (function () {
            var timer = 0;
            return function (callback, ms) {
                clearTimeout(timer);
                timer = setTimeout(callback, ms);
            };
        })();

        $(oe_website_sale_modifier).on("change", ".oe_cart input.js_quantity[data-product-id]", function () {
            var $input = $(this);
            if ($input.data('update_change')) {
                return;
            }
            var value = parseInt($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 1;
            }
            var $dom = $(this).closest('tr');
            //var default_price = parseFloat($dom.find('.text-danger > span.oe_currency_value').text());
            var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
            var line_id = parseInt($input.data('line-id'), 10);
            var product_ids = [parseInt($input.data('product-id'), 10)];
            clickwatch(function () {
                $dom_optional.each(function () {
                    $(this).find('.js_quantity').text(value);
                    product_ids.push($(this).find('span[data-product-id]').data('product-id'));
                });
                $input.data('update_change', true);

                ajax.jsonRpc("/shop/cart/update_json", 'call', {
                    'line_id': line_id,
                    'product_id': parseInt($input.data('product-id'), 10),
                    'set_qty': value
                }).then(function (data) {
                    $input.data('update_change', false);
                    var check_value = parseInt($input.val() || 0, 10);
                    if (isNaN(check_value)) {
                        check_value = 1;
                    }
                    if (value !== check_value) {
                        $input.trigger('change');
                        return;
                    }
                    var $q = $(".my_cart_quantity");
                    if (data.cart_quantity) {
                        $q.parents('li:first').removeClass("hidden");
                    }
                    else {
                        $q.parents('li:first').addClass("hidden");
                        $('a[href*="/shop/checkout"]').addClass("hidden");
                    }

                    $q.html(data.cart_quantity).hide().fadeIn(600);
                    $input.val(data.quantity);
                    $('.js_quantity[data-line-id=' + line_id + ']').val(data.quantity).html(data.quantity);

                    $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();

                    if (data.warning) {
                        var cart_alert = $('.oe_cart').parent().find('#data_warning');
                        if (cart_alert.length === 0) {
                            $('.oe_cart').prepend('<div class="alert alert-danger alert-dismissable" role="alert" id="data_warning">' +
                                '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning + '</div>');
                        }
                        else {
                            cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning);
                        }
                        $input.val(data.quantity);
                    }
                });
            }, 500);
        });

        $(oe_website_sale_modifier).on("click", ".oe_cart a.js_add_suggested_products", function () {
            $(this).prev('input').val(1).trigger('change');
        });

        // hack to add and remove from cart with json
        $(oe_website_sale_modifier).on('click', 'a.js_add_cart_json', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.parent().find("input");
            var product_id = +$input.closest('*:has(input[name="product_id"])').find('input[name="product_id"]').val();
            var min = parseFloat($input.data("min") || 0);
            var max = parseFloat($input.data("max") || Infinity);
            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val() || 0, 10);
            // if they are more of one input for this product (eg: option modal)
            $('input[name="' + $input.attr("name") + '"]').add($input).filter(function () {
                var $prod = $(this).closest('*:has(input[name="product_id"])');
                return !$prod.length || +$prod.find('input[name="product_id"]').val() === product_id;
            }).val(quantity > min ? (quantity < max ? quantity : max) : min);
            $input.change();
            return false;
        });

        $('.oe_website_sale_modifier .a-submit, #comment .a-submit').off('click').on('click', function (event) {
            if (!event.isDefaultPrevented() && !$(this).is(".disabled")) {
                $(this).closest('form').submit();
            }
            if ($(this).hasClass('a-submit-disable')) {
                $(this).addClass("disabled");
            }
            if ($(this).hasClass('a-submit-loading')) {
                var loading = '<span class="fa fa-cog fa-spin"/>';
                var fa_span = $(this).find('span[class*="fa"]');
                if (fa_span.length) {
                    fa_span.replaceWith(loading);
                }
                else {
                    $(this).append(loading);
                }
            }
        });
        $('form.js_attributes input, form.js_attributes select', oe_website_sale_modifier).on('change', function (event) {
            if (!event.isDefaultPrevented()) {
                $(this).closest("form").submit();
            }
        });

        // change price when they are variants
        $('form.js_add_cart_json label', oe_website_sale_modifier).on('mouseup touchend', function () {
            var $label = $(this);
            var $price = $label.parents("form:first").find(".oe_price .oe_currency_value");
            if (!$price.data("price")) {
                $price.data("price", parseFloat($price.text()));
            }
            var value = $price.data("price") + parseFloat($label.find(".badge span").text() || 0);

            var dec = value % 1;
            $price.html(value + (dec < 0.01 ? ".00" : (dec < 1 ? "0" : "") ));
        });
        // hightlight selected color
        $('.css_attribute_color input', oe_website_sale_modifier).on('change', function () {
            $('.css_attribute_color').removeClass("active");
            $('.css_attribute_color:has(input:checked)').addClass("active");
        });

        function price_to_str(price) {
            var l10n = _t.database.parameters;
            var precision = 2;

            if ($(".decimal_precision").length) {
                precision = parseInt($(".decimal_precision").last().data('precision'));
                if (!precision) {
                    precision = 0;
                } //todo: remove me in master/saas-17
            }
            var formatted = _.str.sprintf('%.' + precision + 'f', price).split('.');
            formatted[0] = utils.insert_thousand_seps(formatted[0]);
            return formatted.join(l10n.decimal_point);
        }

        function update_product_image(event_source, product_id) {
            if ($('#o-carousel-product').length) {
                var $img = $(event_source).closest('tr.js_product, .oe_website_sale_modifier').find('img.js_variant_img');
                $img.attr("src", "/web/image/product.product/" + product_id + "/image");
                $img.parent().attr('data-oe-model', 'product.product').attr('data-oe-id', product_id)
                    .data('oe-model', 'product.product').data('oe-id', product_id);

                var $thumbnail = $(event_source).closest('tr.js_product, .oe_website_sale_modifier').find('img.js_variant_img_small');
                if ($thumbnail.length !== 0) { // if only one, thumbnails are not displayed
                    $thumbnail.attr("src", "/web/image/product.product/" + product_id + "/image/90x90");
                    $('.carousel').carousel(0);
                }
            }
            else {
                var $img = $(event_source).closest('tr.js_product, .oe_website_sale_modifier').find('span[data-oe-model^="product."][data-oe-type="image"] img:first, img.product_detail_img');
                $img.attr("src", "/web/image/product.product/" + product_id + "/image");
                $img.parent().attr('data-oe-model', 'product.product').attr('data-oe-id', product_id)
                    .data('oe-model', 'product.product').data('oe-id', product_id);
            }
            // reset zooming constructs
            $img.filter('[data-zoom-image]').attr('data-zoom-image', $img.attr('src'));
            if ($img.data('zoomOdoo') !== undefined) {
                $img.data('zoomOdoo').isReady = false;
            }
        }

        $(oe_website_sale_modifier).on('change', 'input.js_product_change', function () {
            var self = this;
            var $parent = $(this).closest('.js_product');
            $.when(base.ready()).then(function () {
                $parent.find(".oe_default_price:first .oe_currency_value").html(price_to_str(+$(self).data('lst_price')));
                $parent.find(".oe_price:first .oe_currency_value").html(price_to_str(+$(self).data('price')));
            });
            update_product_image(this, +$(this).val());
        });

        $(oe_website_sale_modifier).on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {
            var $ul = $(ev.target).closest('.js_add_cart_variants');
            var $parent = $ul.closest('.js_product');
            var $product_id = $parent.find('.product_id').first();
            var $price = $parent.find(".oe_price:first .oe_currency_value");
            var $default_price = $parent.find(".oe_default_price:first .oe_currency_value");
            var $optional_price = $parent.find(".oe_optional:first .oe_currency_value");
            var variant_ids = $ul.data("attribute_value_ids");
            var list_attribute_value = [];
            var values = [];
            var unchanged_values = $parent.find('div.oe_unchanged_value_ids').data('unchanged_value_ids') || [];
            var js_quantity = $parent.find('table.js_product_size input.js_quantity')
            var js_not_size_quantity = $parent.find('table.js_product_not_size input.js_quantity')
            var js_only_size_quantity = $parent.find('table.js_product_only_size input.js_quantity')
            var js_product_not_have_attribute = $parent.find('table.js_product_not_have_attribute input.js_quantity')

            $parent.find('input.js_variant_change:checked, select.js_variant_change').each(function () {
                values.push(+$(this).val());
            });
            values = values.concat(unchanged_values);

            $parent.find("label").removeClass("text-muted css_not_available");
            for (var k in variant_ids) {
                list_attribute_value.push(variant_ids[k][1])
            }
            var product_id = false;
            var check_qty = false;
            var total_qty = 0
            var total_amount = 0
            if (js_product_not_have_attribute.length != 0) {
                var product_size_id = $parent.find('table.js_product_not_have_attribute a.product_size_id')[0]
                var sp_co_the_ban = $parent.find('table.js_product_not_have_attribute a.sp_co_the_ban')[0]
                var gia_ban_san_pham = $parent.find('table.js_product_not_have_attribute a.gia_ban_san_pham')[0]
                if (gia_ban_san_pham.length != 0 && gia_ban_san_pham.text) {
                    total_amount += parseInt(js_product_not_have_attribute[0].value) * parseInt(gia_ban_san_pham.text)
                }
                total_qty = parseInt(js_product_not_have_attribute[0].value)
                if (!(js_product_not_have_attribute[0].value && js_product_not_have_attribute[0].value != '' && js_product_not_have_attribute[0].value != 0)) {
                    js_product_not_have_attribute[0].value = 0
                }
                else {
                    check_qty = true
                }

                if (variant_ids) {
                    if (parseInt(variant_ids[0][5]) == 1) {
                        if (parseInt(variant_ids[0][4]) <= 0) {
                            // sp_co_the_ban.text = '0'
                            product_size_id.text = variant_ids[0][0]
                            sp_co_the_ban.style.color = "red"
                            sp_co_the_ban.text = 'Cháy hàng'
                            if (gia_ban_san_pham.length != 0) {
                                gia_ban_san_pham.text = variant_ids[0][2]
                            }
                        }
                        else {
                            sp_co_the_ban.style.color = "green"
                            sp_co_the_ban.text = variant_ids[0][4]
                            product_size_id.text = variant_ids[0][0]
                            // product_status_qty.style.color = "green"
                            // product_status_qty.text = 'Còn hàng'
                            if (gia_ban_san_pham.length != 0) {
                                gia_ban_san_pham.text = variant_ids[0][2]
                            }
                        }
                    }

                    else {
                        if (parseInt(variant_ids[0][5]) == 3) {
                            if (parseInt(variant_ids[0][4]) <= 0) {
                                product_size_id.text = variant_ids[0][0]
                                sp_co_the_ban.style.color = "red"
                                sp_co_the_ban.text = 'Cháy hàng'
                                if (gia_ban_san_pham.length != 0) {
                                    gia_ban_san_pham.text = variant_ids[0][2]
                                }
                            }
                            else {
                                product_size_id.text = variant_ids[0][0]
                                sp_co_the_ban.style.color = "green"
                                sp_co_the_ban.text = 'Còn hàng'
                                if (gia_ban_san_pham.length != 0) {
                                    gia_ban_san_pham.text = variant_ids[0][2]
                                }
                            }
                        }
                        else {
                            if (parseInt(variant_ids[0][4]) <= 0) {
                                product_size_id.text = variant_ids[0][0]
                                sp_co_the_ban.style.color = "red"
                                sp_co_the_ban.text = 'Cháy hàng'
                                if (gia_ban_san_pham.length != 0) {
                                    gia_ban_san_pham.text = variant_ids[0][2]
                                }
                            }
                            else {
                                if (parseInt(variant_ids[0][4]) < parseInt(variant_ids[0][6])) {
                                    sp_co_the_ban.style.color = "green"
                                    sp_co_the_ban.text = variant_ids[0][4]
                                    product_size_id.text = variant_ids[0][0]
                                    if (gia_ban_san_pham.length != 0) {
                                        gia_ban_san_pham.text = variant_ids[0][2]
                                    }
                                }
                                else {
                                    sp_co_the_ban.style.color = "green"
                                    sp_co_the_ban.text = _.str.sprintf(_t(">%s"), variant_ids[0][6])
                                    product_size_id.text = variant_ids[0][0]
                                    if (gia_ban_san_pham.length != 0) {
                                        gia_ban_san_pham.text = variant_ids[0][2]
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (js_not_size_quantity.length == 1) {
                var product_size_id = $parent.find('table.js_product_not_size a.product_size_id')[0]
                var sp_co_the_ban = $parent.find('table.js_product_not_size a.sp_co_the_ban')[0]
                var gia_ban_san_pham = $parent.find('table.js_product_not_size a.gia_ban_san_pham')[0]
                var tr_attribute_value = $parent.find('table.js_product_not_size tr.js_product_quantity')[0]
                var active = false;
                if (gia_ban_san_pham.length != 0 && gia_ban_san_pham.text) {
                    total_amount += parseInt(js_not_size_quantity[0].value) * parseInt(gia_ban_san_pham.text)
                }
                total_qty = parseInt(js_not_size_quantity[0].value)
                if (!(js_not_size_quantity[0].value && js_not_size_quantity[0].value != '' && js_not_size_quantity[0].value != 0)) {
                    js_not_size_quantity[0].value = 0
                }
                else {
                    check_qty = true
                }
                for (var i = 0; i < list_attribute_value.length; i++) {
                    if (_.isEqual(list_attribute_value[i], values)) {
                        active = true;
                    }
                }
                if (active == true) {
                    tr_attribute_value.classList.remove('hidden');
                    for (var k in variant_ids) {
                        if (_.isEmpty(_.difference(variant_ids[k][1], values))) {
                            if (parseInt(variant_ids[k][5]) == 1) {
                                if (parseInt(variant_ids[k][4]) <= 0) {
                                    // sp_co_the_ban.text = '0'
                                    product_size_id.text = variant_ids[k][0]
                                    sp_co_the_ban.style.color = "red"
                                    sp_co_the_ban.text = 'Cháy hàng'
                                    if (gia_ban_san_pham.length != 0) {
                                        gia_ban_san_pham.text = variant_ids[k][2]
                                    }
                                }
                                else {
                                    sp_co_the_ban.style.color = "green"
                                    sp_co_the_ban.text = variant_ids[k][4]
                                    product_size_id.text = variant_ids[k][0]
                                    // product_status_qty.style.color = "green"
                                    // product_status_qty.text = 'Còn hàng'
                                    if (gia_ban_san_pham.length != 0) {
                                        gia_ban_san_pham.text = variant_ids[k][2]
                                    }
                                }
                            }

                            else {
                                if (parseInt(variant_ids[k][5]) == 3) {
                                    if (parseInt(variant_ids[k][4]) <= 0) {
                                        product_size_id.text = variant_ids[k][0]
                                        sp_co_the_ban.style.color = "red"
                                        sp_co_the_ban.text = 'Cháy hàng'
                                        if (gia_ban_san_pham.length != 0) {
                                            gia_ban_san_pham.text = variant_ids[k][2]
                                        }
                                    }
                                    else {
                                        product_size_id.text = variant_ids[k][0]
                                        sp_co_the_ban.style.color = "green"
                                        sp_co_the_ban.text = 'Còn hàng'
                                        if (gia_ban_san_pham.length != 0) {
                                            gia_ban_san_pham.text = variant_ids[k][2]
                                        }
                                    }
                                }
                                else {
                                    if (parseInt(variant_ids[k][4]) <= 0) {
                                        product_size_id.text = variant_ids[k][0]
                                        sp_co_the_ban.style.color = "red"
                                        sp_co_the_ban.text = 'Cháy hàng'
                                        if (gia_ban_san_pham.length != 0) {
                                            gia_ban_san_pham.text = variant_ids[k][2]
                                        }
                                    }
                                    else {
                                        if (parseInt(variant_ids[k][4]) < parseInt(variant_ids[k][6])) {
                                            sp_co_the_ban.style.color = "green"
                                            sp_co_the_ban.text = variant_ids[k][4]
                                            product_size_id.text = variant_ids[k][0]
                                            if (gia_ban_san_pham.length != 0) {
                                                gia_ban_san_pham.text = variant_ids[k][2]
                                            }
                                        }
                                        else {
                                            sp_co_the_ban.style.color = "green"
                                            sp_co_the_ban.text = _.str.sprintf(_t(">%s"), variant_ids[k][6])
                                            product_size_id.text = variant_ids[k][0]
                                            if (gia_ban_san_pham.length != 0) {
                                                gia_ban_san_pham.text = variant_ids[k][2]
                                            }
                                        }
                                    }
                                }
                            }
                            break;
                        }
                    }
                } else {
                    tr_attribute_value.classList.add('hidden');
                }
            }

            if (js_only_size_quantity.length != 0) {
                for (var q = 0; q < js_only_size_quantity.length; q++) {
                    var product_size_id = $parent.find('table.js_product_only_size a.product_size_id')[q]
                    var sp_co_the_ban = $parent.find('table.js_product_only_size a.sp_co_the_ban')[q]
                    var gia_ban_san_pham = $parent.find('table.js_product_only_size a.gia_ban_san_pham')[q]
                    var product_status_qty = $parent.find('table.js_product_only_size a.product_status_qty')[q]
                    var tr_attribute_value = $parent.find('table.js_product_only_size tr.js_product_quantity')[q]
                    var active = false;
                    var attribute_value_id = parseInt(product_size_id.getAttribute('value_id'));
                    total_qty += parseInt(js_only_size_quantity[q].value)
                    if (gia_ban_san_pham.length != 0 && gia_ban_san_pham.text) {
                        total_amount += parseInt(js_only_size_quantity[q].value) * parseInt(gia_ban_san_pham.text)
                    }

                    if (!(js_only_size_quantity[q].value && js_only_size_quantity[q].value != '' && js_only_size_quantity[q].value != 0)) {
                        js_only_size_quantity[q].value = 0
                    }
                    else {
                        check_qty = true
                    }
                    for (var i = 0; i < list_attribute_value.length; i++) {
                        if (_.isEqual(list_attribute_value[i], [attribute_value_id])) {
                            active = true;
                        }
                    }

                    if (active == true) {
                        tr_attribute_value.classList.remove('hidden');
                        for (var k in variant_ids) {
                        if (parseInt(variant_ids[k][5]) == 1) {
                            if (parseInt(variant_ids[k][4]) <= 0) {
                                // sp_co_the_ban.text = '0'
                                product_size_id.text = variant_ids[k][0]
                                sp_co_the_ban.style.color = "red"
                                sp_co_the_ban.text = 'Cháy hàng'
                                if (gia_ban_san_pham.length != 0) {
                                    gia_ban_san_pham.text = variant_ids[k][2]
                                }
                            }
                            else {
                                sp_co_the_ban.style.color = "green"
                                sp_co_the_ban.text = variant_ids[k][4]
                                product_size_id.text = variant_ids[k][0]
                                // product_status_qty.style.color = "green"
                                // product_status_qty.text = 'Còn hàng'
                                if (gia_ban_san_pham.length != 0) {
                                    gia_ban_san_pham.text = variant_ids[k][2]
                                }
                            }
                        }

                        else {
                            if (parseInt(variant_ids[k][5]) == 3) {
                                if (parseInt(variant_ids[k][4]) <= 0) {
                                    product_size_id.text = variant_ids[k][0]
                                    sp_co_the_ban.style.color = "red"
                                    sp_co_the_ban.text = 'Cháy hàng'
                                    if (gia_ban_san_pham.length != 0) {
                                        gia_ban_san_pham.text = variant_ids[k][2]
                                    }
                                }
                                else {
                                    product_size_id.text = variant_ids[k][0]
                                    sp_co_the_ban.style.color = "green"
                                    sp_co_the_ban.text = 'Còn hàng'
                                    if (gia_ban_san_pham.length != 0) {
                                        gia_ban_san_pham.text = variant_ids[k][2]
                                    }
                                }
                            }
                            else {
                                if (parseInt(variant_ids[k][4]) <= 0) {
                                    product_size_id.text = variant_ids[k][0]
                                    sp_co_the_ban.style.color = "red"
                                    sp_co_the_ban.text = 'Cháy hàng'
                                    if (gia_ban_san_pham.length != 0) {
                                        gia_ban_san_pham.text = variant_ids[k][2]
                                    }
                                }
                                else {
                                    if (parseInt(variant_ids[k][4]) < parseInt(variant_ids[k][6])) {
                                        sp_co_the_ban.style.color = "green"
                                        sp_co_the_ban.text = variant_ids[k][4]
                                        product_size_id.text = variant_ids[k][0]
                                        if (gia_ban_san_pham.length != 0) {
                                            gia_ban_san_pham.text = variant_ids[k][2]
                                        }
                                    }
                                    else {
                                        sp_co_the_ban.style.color = "green"
                                        sp_co_the_ban.text = _.str.sprintf(_t(">%s"), variant_ids[k][6])
                                        product_size_id.text = variant_ids[k][0]
                                        if (gia_ban_san_pham.length != 0) {
                                            gia_ban_san_pham.text = variant_ids[k][2]
                                        }
                                    }
                                }
                            }
                        }
                        update_product_image(this, product_id);
                        break;
                    }
                    } else {
                        tr_attribute_value.classList.add('hidden');
                    }
                    
                    // }
                }
            }

            if (js_quantity.length != 0) {
                for (var q = 0; q < js_quantity.length; q++) {
                    var product_size_id = $parent.find('table.js_product_size a.product_size_id')[q]
                    var sp_co_the_ban = $parent.find('table.js_product_size a.sp_co_the_ban')[q]
                    var gia_ban_san_pham = $parent.find('table.js_product_size a.gia_ban_san_pham')
                    var product_status_qty = $parent.find('table.js_product_size a.product_status_qty')[q]
                    var total_amount_product = $parent.find('b.total_amount_product')
                    var tr_attribute_value = $parent.find('table.js_product_size tr.js_product_quantity')[q]
                    var variant_id = js_quantity[q].name.split('-')[2]
                    var values_full = []
                    var active = false;

                    total_qty += parseInt(js_quantity[q].value)
                    if (gia_ban_san_pham.length != 0 && gia_ban_san_pham[q].text) {
                        total_amount += parseInt(js_quantity[q].value) * parseInt(gia_ban_san_pham[q].text)
                    }

                    $parent.find('input.js_variant_change:checked, select.js_variant_change').each(function () {
                        values_full.push(+$(this).val());
                    });
                    values_full.push(parseInt(variant_id))
                    if (!(js_quantity[q].value && js_quantity[q].value != '' && js_quantity[q].value != 0)) {
                        js_quantity[q].value = 0
                    }
                    else {
                        check_qty = true
                    }
                    for (var i = 0; i < list_attribute_value.length; i++) {
                        if (_.isEqual(list_attribute_value[i], values_full)) {
                            active = true;
                        }
                    }
                    if (active == true) {
                        tr_attribute_value.classList.remove('hidden');
                        for (var k in variant_ids) {
                            if (_.isEmpty(_.difference(variant_ids[k][1], values_full))) {
                                if (parseInt(variant_ids[k][5]) == 1) {
                                    if (parseInt(variant_ids[k][4]) <= 0) {
                                        // sp_co_the_ban.text = '0'
                                        product_size_id.text = variant_ids[k][0]
                                        sp_co_the_ban.style.color = "red"
                                        sp_co_the_ban.text = 'Cháy hàng'
                                        if (gia_ban_san_pham.length != 0) {
                                            gia_ban_san_pham[q].text = variant_ids[k][2]
                                        }
                                    }
                                    else {
                                        sp_co_the_ban.style.color = "green"
                                        sp_co_the_ban.text = variant_ids[k][4]
                                        product_size_id.text = variant_ids[k][0]
                                        // product_status_qty.style.color = "green"
                                        // product_status_qty.text = 'Còn hàng'
                                        if (gia_ban_san_pham.length != 0) {
                                            gia_ban_san_pham[q].text = variant_ids[k][2]
                                        }
                                    }
                                }

                                else {
                                    if (parseInt(variant_ids[k][5]) == 3) {
                                        if (parseInt(variant_ids[k][4]) <= 0) {
                                            product_size_id.text = variant_ids[k][0]
                                            sp_co_the_ban.style.color = "red"
                                            sp_co_the_ban.text = 'Cháy hàng'
                                            if (gia_ban_san_pham.length != 0) {
                                                gia_ban_san_pham[q].text = variant_ids[k][2]
                                            }
                                        }
                                        else {
                                            product_size_id.text = variant_ids[k][0]
                                            sp_co_the_ban.style.color = "green"
                                            sp_co_the_ban.text = 'Còn hàng'
                                            if (gia_ban_san_pham.length != 0) {
                                                gia_ban_san_pham[q].text = variant_ids[k][2]
                                            }
                                        }
                                    }
                                    else {
                                        if (parseInt(variant_ids[k][4]) <= 0) {
                                            product_size_id.text = variant_ids[k][0]
                                            sp_co_the_ban.style.color = "red"
                                            sp_co_the_ban.text = 'Cháy hàng'
                                            if (gia_ban_san_pham.length != 0) {
                                                gia_ban_san_pham[q].text = variant_ids[k][2]
                                            }
                                        }
                                        else {
                                            if (parseInt(variant_ids[k][4]) < parseInt(variant_ids[k][6])) {
                                                sp_co_the_ban.style.color = "green"
                                                sp_co_the_ban.text = variant_ids[k][4]
                                                product_size_id.text = variant_ids[k][0]
                                                if (gia_ban_san_pham.length != 0) {
                                                    gia_ban_san_pham[q].text = variant_ids[k][2]
                                                }
                                            }
                                            else {
                                                sp_co_the_ban.style.color = "green"
                                                sp_co_the_ban.text = _.str.sprintf(_t(">%s"), variant_ids[k][6])
                                                product_size_id.text = variant_ids[k][0]
                                                if (gia_ban_san_pham.length != 0) {
                                                    gia_ban_san_pham[q].text = variant_ids[k][2]
                                                }
                                            }
                                        }
                                    }
                                }
                                update_product_image(this, product_id);
                                break;
                            }
                        }
                    } else {
                        tr_attribute_value.classList.add('hidden');
                    }

                    // }
                }
            }
            var total_qty_html = $parent.find('input.total_qty')
            var total_price_html = $parent.find('input.total_price')
            if (total_qty_html.length != 0 && total_price_html.length != 0) {
                total_qty_html.val(total_qty)
                total_price_html.val(String(total_amount) + " đ")
            }

            $parent.find("input.js_variant_change:radio, select.js_variant_change").each(function () {
                var $input = $(this);
                var id = +$input.val();
                var values = [id];

                $parent.find("ul:not(:has(input.js_variant_change[value='" + id + "'])) input.js_variant_change:checked, select.js_variant_change").each(function () {
                    values.push(+$(this).val());
                });

                for (var k in variant_ids) {
                    if (!_.difference(values, variant_ids[k][1]).length) {
                        return;
                    }
                }
                $input.closest("label").addClass("css_not_available");
                $input.find("option[value='" + id + "']").addClass("css_not_available");
            });

            if (product_id || check_qty) {
                $parent.removeClass("css_not_available");
                $parent.find("#add_to_cart").removeClass("disabled");
                if (product_id) {
                    $product_id.val(product_id);
                }
                else {
                    $product_id.val(0);
                }
            } else {
                $parent.addClass("css_not_available");
                $product_id.val(0);
                $parent.find("#add_to_cart").addClass("disabled");
            }
        });

        $('div.js_product', oe_website_sale_modifier).each(function () {
            $('input.js_product_change', this).first().trigger('change');
            $('input.js_quantity', this).first().trigger('change');
        });

        $('.js_add_cart_variants', oe_website_sale_modifier).each(function () {
            $('input.js_variant_change, select.js_variant_change', this).first().trigger('change');
        });

        $('.oe_cart').on('click', '.js_change_shipping', function () {
            if (!$('body.editor_enable').length) { //allow to edit button text with editor
                var $old = $('.all_shipping').find('.panel.border_primary');
                $old.find('.btn-ship').toggle();
                $old.addClass('js_change_shipping');
                $old.removeClass('border_primary');

                var $new = $(this).parent('div.one_kanban').find('.panel');
                $new.find('.btn-ship').toggle();
                $new.removeClass('js_change_shipping');
                $new.addClass('border_primary');

                var $form = $(this).parent('div.one_kanban').find('form.hide');
                $.post($form.attr('action'), $form.serialize() + '&xhr=1');
            }
        });
        $('.oe_cart').on('click', '.js_edit_address', function () {
            $(this).parent('div.one_kanban').find('form.hide').attr('action', '/shop/address').submit();
        });
        $('.oe_cart').on('click', '.js_delete_product', function (e) {
            e.preventDefault();
            $(this).closest('tr').find('.js_quantity').val(0).trigger('change');
        });

        if ($('.oe_website_sale_modifier .dropdown_sorty_by').length) {
            // this method allow to keep current get param from the action, with new search query
            $('.oe_website_sale_modifier .o_website_sale_search').on('submit', function (event) {
                var $this = $(this);
                if (!event.isDefaultPrevented() && !$this.is(".disabled")) {
                    event.preventDefault();
                    var oldurl = $this.attr('action');
                    oldurl += (oldurl.indexOf("?") === -1) ? "?" : "";
                    var search = $this.find('input.search-query');
                    window.location = oldurl + '&' + search.attr('name') + '=' + encodeURIComponent(search.val());
                }
            });
        }

        if ($(".checkout_autoformat").length) {
            $(oe_website_sale_modifier).on('change', "select[name='country_id']", function () {
                clickwatch(function () {
                    if ($("#country_id").val()) {
                        ajax.jsonRpc("/shop/country_infos/" + $("#country_id").val(), 'call', {mode: 'shipping'}).then(
                            function (data) {
                                // placeholder phone_code
                                //$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

                                // populate states and display
                                var selectStates = $("select[name='state_id']");
                                // dont reload state at first loading (done in qweb)
                                if (selectStates.data('init') === 0 || selectStates.find('option').length === 1) {
                                    if (data.states.length) {
                                        selectStates.html('');
                                        _.each(data.states, function (x) {
                                            var opt = $('<option>').text(x[1])
                                                .attr('value', x[0])
                                                .attr('data-code', x[2]);
                                            selectStates.append(opt);
                                        });
                                        selectStates.parent('div').show();
                                    }
                                    else {
                                        selectStates.val('').parent('div').hide();
                                    }
                                    selectStates.data('init', 0);
                                }
                                else {
                                    selectStates.data('init', 0);
                                }

                                // manage fields order / visibility
                                if (data.fields) {
                                    if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)) {
                                        $(".div_zip").before($(".div_city"));
                                    }
                                    else {
                                        $(".div_zip").after($(".div_city"));
                                    }
                                    var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                                    _.each(all_fields, function (field) {
                                        $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields) >= 0);
                                    });
                                }
                            }
                        );
                    }
                }, 500);
            });
        }
        $("select[name='country_id']").change();
    });
});


$(document).ready(function () {
    odoo.define('website_sale.website_sale', function (require) {
        "use strict";

        $('.oe_website_sale').each(function () {
            var oe_website_sale = this;
            var ajax = require('web.ajax');

            $(oe_website_sale).on('click', 'a.js_add_cart_all_json', function (ev) {
                ev.preventDefault();
                var $link = $(ev.currentTarget);
                var $input = $link.parent().find("input");
                var product_id = +$input.closest('*:has(input[name="product_id"])').find('input[name="product_id"]').val();
                var product_str = $input[0].getAttribute('data-product-id');
                var span = $link.parents().find('span.' + product_str);
                var span_qty = parseFloat($link.parents().find('span.' + product_str).html()) + ($link.has(".fa-minus").length ? 1 : -1);
                var min = parseFloat($input.data("min") || 0);
                var max = parseFloat($input.data("max") || Infinity);
                var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val() || 0, 10);
                // if they are more of one input for this product (eg: option modal)
                if (span_qty < 0) {
                    $('input[name="' + $input.attr("name") + '"]').add($input).filter(function () {
                        var $prod = $(this).closest('*:has(input[name="product_id"])');
                        return !$prod.length || +$prod.find('input[name="product_id"]').val() === product_id;
                    }).val(parseFloat($input.val() || 0, 10) > min ? (parseFloat($input.val() || 0, 10) < max ? parseFloat($input.val() || 0, 10) : max) : min);
                    $input.change();
                    return false;
                }
                if (quantity >= 0) {
                    span.html(span_qty);
                }

                $('input[name="' + $input.attr("name") + '"]').add($input).filter(function () {
                    var $prod = $(this).closest('*:has(input[name="product_id"])');
                    return !$prod.length || +$prod.find('input[name="product_id"]').val() === product_id;
                }).val(quantity > min ? (quantity < max ? quantity : max) : min);
                $input.change();
                return false;
            });

            $(oe_website_sale).on("click", ".oe_cart .js_cart_delete", function () {
                console.log('click delete 2');
                var $input = $(this);
                var line_id = parseInt($(this).data('product_tmpl_line-id'), 10);
                ajax.jsonRpc("/shop/cart/delete_cart", 'call', {
                    'line_id': line_id,
                }).then(function (data) {
                    var $q = $(".my_cart_quantity");
                    $q.html(data.cart_quantity).hide().fadeIn(600);
                    $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
                });
            });

            $(oe_website_sale).on("click", ".oe_cart .js_cart_update_all", function () {
                console.log('click update 1');
                var js_quantity = $('table.table-condensed input.js_quantity_all')
                var $input = $(this);
                var product_tmpl_line_id = parseInt($(this).data('product_tmpl_line-id'), 10);
                var product_ids = []
                if (js_quantity.length != 0) {
                    for (var q = 0; q < js_quantity.length; q++) {

                        var quantity_list = parseInt(js_quantity[q].value)
                        var input_product_tmpl_line_id = parseInt(js_quantity[q].getAttribute('data-product_tmpl_line-id'))
                        var line_id = parseInt(js_quantity[q].getAttribute('data-line-id'))
                        var product_id = parseInt(js_quantity[q].getAttribute('data-product-id'))
                        if (input_product_tmpl_line_id == product_tmpl_line_id) {
                            product_ids.push({
                                line_id: line_id,
                                product_id: product_id,
                                value: quantity_list
                            })
                        }

                    }
                }
                ajax.jsonRpc("/shop/cart/update_all_cart", 'call', {
                    'product_tmpl_line_id': product_tmpl_line_id,
                    'line_data': product_ids,
                }).then(function (data) {
                    var $q = $(".my_cart_quantity");
                    $q.html(data.cart_quantity).hide().fadeIn(600);
                    $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
                });
            });
        });

        $('.js_quantity_all').click(function () {
            console.log('click');
            return false;
        });

        $(".js_quantity_all").on("input", function () {
            console.log('input');
            var $input = $(this);
            var qty = parseInt($(this).val() || '0', 10);
            var product_id = $input[0].getAttribute('data-product-id');
            var span = $input.parents().find('span.' + product_id);
            var span_qty = parseFloat($input.parents().find('span.' + product_id).html());
            var product_uom_qty = parseInt($input[0].getAttribute('product_uom_qty'), 10);
            var total_qty = product_uom_qty + span_qty
            if (total_qty >= qty) {
                span.html(total_qty - qty);
                $input[0].setAttribute('product_uom_qty', qty);
            }
            else {
                span.html(0);
                $input[0].setAttribute('product_uom_qty', total_qty);
                $(this).val(total_qty);
            }
        });
    });
});