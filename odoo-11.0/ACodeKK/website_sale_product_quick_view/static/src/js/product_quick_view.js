odoo.define('website_sale_product_quick_view.website_sale', function(require) {
"use strict";

var ajax = require('web.ajax');
var website = require('website.website');
var base = require('web_editor.base');
var core = require('web.core');
var Model = require('web.Model');
var _t = core._t;
var session = require('web.session');

// when clicking the button start the timeline/animation:
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
            new Model("product.interest").call("change_product_interest_list",[1,product,'remove'])
        } else {
            $(this).addClass('active');
            new Model("product.interest").call("change_product_interest_list",[1,product,'add'])
        }
    }
});


$('.oe_website_sale #products_grid #product_quick_view')
    .click(_.debounce(function (event) {
            var $form = $(this).closest('form');
            var product_id = this.dataset.target;
            var self = this
            event.preventDefault();
            var popup_add_to_cart = $('.popup_add_to_cart')
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
                                        var $warning = $(quantity);
                                        $warning.appendTo($('.oe_website_sale')).modal()
                                        return false
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
                            // $input.closest("label").addClass("css_not_available");
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
});
