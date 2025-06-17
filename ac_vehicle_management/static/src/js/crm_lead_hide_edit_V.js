odoo.define('ac_vehicle_management.crm_lead_hide_edit_V', function(require) {
    "use strict";
    console.log('DONE')
    var FormController = require('web.FormController');

    FormController.include({
        _updateButtons: function() {
            this._super.apply(this, arguments);

            if (this.modelName === 'crm.lead' && this.$buttons) {
                var activeField = this.renderer.state.data.active;
                var teamField = this.renderer.state.data.team_id.data.display_name;
                console.log(teamField);
                if (activeField === false && teamField === 'Sales') {
                    this.$buttons.find('.o_form_button_edit').hide();
                } else {
                    this.$buttons.find('.o_form_button_edit').show();  // ensure it appears again if needed
                }
            }
        },
    });
});
