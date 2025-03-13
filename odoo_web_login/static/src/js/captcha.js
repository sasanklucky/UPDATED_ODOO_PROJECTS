odoo.define('odoo_web_login.captcha', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    function reloadCaptcha() {
        ajax.jsonRpc("/captcha/generate", 'call', {}).then(function (data) {
            $("#captcha_image").attr("src", "data:image/png;base64," + data.captcha_image);
        });
    }

    // Expose reloadCaptcha globally
    window.reloadCaptcha = reloadCaptcha;

    $(document).ready(function () {
        reloadCaptcha();
        console.log("KRISHNAAAA");

        $('form').on('submit', function (e) {
            var captchaInput = $('#captcha_input').val();
            console.log(captchaInput, 'bb')
            if (!captchaInput) {
                e.preventDefault();
                alert("Please enter CAPTCHA.");
                return false;
            }

            ajax.jsonRpc("/captcha/validate", 'call', { user_input: captchaInput }).then(function (response) {
                if (!response.success) {
                    e.preventDefault();
                    alert(response.message);
                    reloadCaptcha();
                }
            });

        });
    });
});
