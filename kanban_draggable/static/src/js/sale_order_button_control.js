odoo.define('kanban_draggable.sale_order_button_control', function (require) {
    "use strict";

    const ListController = require('web.ListController');
    const FormController = require('web.FormController');
    const rpc = require('web.rpc');

    function isCrmInactive(context) {
        if (context.from_crm && context.active_id) {
            return rpc.query({
                model: 'crm.lead',
                method: 'read',
                args: [[context.active_id], ['active']],
            }).then(result => {
                if (result && result.length) {
                    return result[0].active === false;
                }
            });
        }
        return Promise.resolve(false);
    }

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            const context = this.initialState.context;

            isCrmInactive(context).then(inactive => {
                if (inactive && this.$buttons) {
                    this.$buttons.find('.o_list_button_add').hide();
                    this.$buttons.find('.o_button_edit').hide();
                }
            });
        },
    });

    FormController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            const context = this.initialState.context;

            isCrmInactive(context).then(inactive => {
                if (inactive && this.$buttons) {
                    this.$buttons.find('.o_form_button_edit').hide();
                    this.$buttons.find('.o_form_button_create').hide();
                    this.$buttons.find('.o_form_button_create_and_edit').hide();
                }
            });
        },
    });

});
