odoo.define("website_search_autocomplete.custom_search", function (require) {
    "use strict";
    var Model = require('web.Model');

    require('website_sale.website_sale');

    $('#search_autocomplete').devbridgeAutocomplete({
        serviceUrl: '/shop/get_suggest',
        minChars: 0,
        onSelect: function (suggestion) {
            var model = new Model("product.search.keyword");
            model.call('do_action', [suggestion]);
            window.location.replace(window.location.origin + '/shop?'
                // + '/shop/product/' + suggestion.data.id
                + '&search=' + suggestion.value);
        }
    });

    // $('#search_autocomplete').devbridgeAutocomplete({
    //     lookup: [{value: 'California', data: 'CA'},],
    //     minChars: 0,
    //     onSelect: function (suggestion) {
    //         var model = new Model("product.search.keyword");
    //         model.call('do_action', [suggestion]);
    //         window.location.replace(window.location.origin + '/shop?'
    //             // + '/shop/product/' + suggestion.data.id
    //             + '&search=' + suggestion.value);
    //     }
    // });



    // $('#search_autocomplete').focus(function () {
    //     console.log('focus');
    //     $('#search_autocomplete').devbridgeAutocomplete({
    //         serviceUrl: '/shop/get_suggest',
    //         onSelect: function (suggestion) {
    //             var model = new Model("product.search.keyword");
    //             model.call('do_action', [suggestion]);
    //             window.location.replace(window.location.origin + '/shop?'
    //                 // + '/shop/product/' + suggestion.data.id
    //                 + '&search=' + suggestion.value);
    //         }
    //     });
    // });
});