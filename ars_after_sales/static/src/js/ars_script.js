odoo.define('ars_after_sales', function (require) {
"use strict";

    var ajax = require('web.ajax');
    $(document).ready(function() {
        console.log('called')
        $('.o_website_form_send').click(function(){
            var vals = {};
            vals['ars_warranty_price'] = $(this).closest('tr').find('input[name=ars_warranty_price]').val();
            vals['comment'] = $(this).closest('tr').find('input[name=comment]').val();
            if ($(this).hasClass('approved')){
                vals['apr_action'] = 'approved'
                $(this).parent().find('.btn-lg').removeClass('green')
                $(this).addClass('green')
            }
            if ($(this).hasClass('reject')){
                vals['apr_action'] = 'reject'
                $(this).parent().find('.btn-lg').removeClass('green')
                $(this).addClass('green')
            }
            if ($(this).hasClass('hold')){
                vals['apr_action'] = 'hold'
                $(this).parent().find('.btn-lg').removeClass('green')
                $(this).addClass('green')
            }
            if ($(this).hasClass('resub')){
                vals['apr_action'] = 're_submission'
                $(this).parent().find('.btn-lg').removeClass('green')
                $(this).addClass('green')
            }
            console.log('vlas===============',vals)

            ajax.jsonRpc("/Warranty-Claim/Update", 'call', {'db_id':$(this).data('dbid'), 'warranty_id':$(this).data('warranty_id'), 'vals': vals})
                    .then(function (data) {

                    });
        })

    });

});
