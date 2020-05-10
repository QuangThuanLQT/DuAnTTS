odoo.define('tts_sale_config_commision.tree_view_button', function (require) {

    var core = require('web.core');
    var ListView = require('web.ListView');
    var QWeb = core.qweb;
    var session = require('web.session');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');

    ListView.include({

        render_buttons: function ($node) {
            var self = this;
            this._super($node);

            if (self.model == 'product.product' && self.ViewManager.action && self.ViewManager.action.xml_id == 'tts_sale_config_commision.product_commision_action') {
                setTimeout(function () {
                   $('.sky-search').addClass('hidden')
                    $('.o_product_buttons_print_excel').addClass('hidden')
                }, 500)
                setTimeout(function () {
                   $('.sky-search').addClass('hidden')
                }, 1500)
            }
        },
    });

});