odoo.define('web_export_view.booking_stage_mask', function (require) {
    "use strict";

    var registry = require('web.field_registry');
    var basicFields = require('web.basic_fields');

    var BookingStageMask = basicFields.FieldChar.extend({
        template: 'BookingStageMaskTemplate', // We'll define this in XML

        events: _.extend({}, basicFields.FieldChar.prototype.events, {
            'click .toggle-visibility': '_toggleVisibility'
        }),

        _render: function () {
            this._super();
            var actualValue = this.value || '';  // Get actual value

            this.$el.html(`
                <div class="o_input_wrapper">
                        <div class="input-container">
                            <input type="password" class="o_input masked-input" value="${actualValue}"/>
                            <span class="toggle-visibility">
                                <i class="fa fa-eye"></i>
                            </span>
                        </div>
                </div>
            `);

            // Store actual value
            this.$input = this.$el.find('.masked-input'); // Set input reference
        },

        _toggleVisibility: function (event) {
            event.preventDefault();
            var $input = this.$el.find('.masked-input');
            var $icon = this.$el.find('.toggle-visibility i');

            if ($input.attr('type') === 'password') {
                $input.attr('type', 'text'); // Show actual value
                $icon.removeClass('fa-eye').addClass('fa-eye-slash');
            } else {
                $input.attr('type', 'password'); // Mask value
                $icon.removeClass('fa-eye-slash').addClass('fa-eye');
            }
        }
    });

    registry.add('booking_stage_mask', BookingStageMask);
});
