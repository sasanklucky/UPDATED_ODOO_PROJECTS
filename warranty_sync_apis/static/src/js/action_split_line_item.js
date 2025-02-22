odoo.define('warranty_sync_apis.action_split_line_item', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var Sidebar = require('web.Sidebar');
    var core = require('web.core');
    var _t = core._t;
    var split_invoice = require('warranty_sync_apis.DataLineItemSplit');

    // Inherit the existing ListController and extend the renderSidebar method
    ListController.include({
        renderSidebar: function ($node) {
            this._super.apply(this, arguments); // Call the original renderSidebar method

            if (this.modelName == 'sale.order.line') {
                // Add your custom "Split Line Items" option
                var other = this.sidebar.options.actions.other || []; // Ensure the actions array exists
                other.push({
                    label: _t("Split Line Items"),
                    callback: this._lineItemsSplitting.bind(this)
                });

                // Reinitialize the sidebar with the updated actions
                this.sidebar = new Sidebar(this, {
                    editable: this.is_action_enabled('edit'),
                    env: {
                        context: this.model.get(this.handle, {raw: true}).getContext(),
                        activeIds: this.getSelectedIds(),
                        model: this.modelName,
                    },
                    actions: {
                        other: other
                    },
                });

                this.sidebar.appendTo($node);
                this._toggleSidebar();
            }
        },

        _lineItemsSplitting: function () {
            // Implement the functionality for "Split Line Items"
            console.log("Split Line Items clicked!");
            var record = this.model.get(this.handle);
            var selected_records = this.getSelectedIds();
            var context = this.model.get(this.handle, {raw: true}).getContext();
            console.log("Context Values:", context);
            if (context) {
                new split_invoice(this, record, selected_records, context).open();
            } else {
                console.error("Context is undefined!");
            }
            // Add your logic here
        },
    });
});


