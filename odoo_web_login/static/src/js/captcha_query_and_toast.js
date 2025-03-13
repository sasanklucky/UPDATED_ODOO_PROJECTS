odoo.define("odoo_web_login.captcha_query_and_toast", function (require) {
    "use strict";

    var ajax = require("web.ajax");
    var core = require("web.core");

    // Load reCAPTCHA dynamically
    (function () {
        if (!window.grecaptcha) {
            var recaptchaScript = document.createElement("script");
            recaptchaScript.src =
                "https://www.google.com/recaptcha/api.js?onload=recaptchaLoaded&render=explicit";
            recaptchaScript.async = true;
            recaptchaScript.defer = true;
            document.head.appendChild(recaptchaScript);
        }
    })();

    // Load Toastify dynamically if not already loaded
    (function () {
        if (!window.Toastify) {
            var toastifyScript = document.createElement("script");
            toastifyScript.src = "https://cdn.jsdelivr.net/npm/toastify-js";
            toastifyScript.async = true;
            document.head.appendChild(toastifyScript);
        }
    })();

    // Callback function when reCAPTCHA script loads
    window.recaptchaLoaded = function () {
        grecaptcha.render("recaptcha-container", {
            sitekey: "6LeRC_EqAAAAAD4kBTqv-C4Uzy701In3PTJkRCIX", // Replace with your actual site key
        });
    };

    // Function to show toast notifications
    function showNotification(text, background) {
        if (!window.Toastify) {
            console.error("Toastify.js not loaded!");
            return;
        }

        Toastify({
            text: text,
            duration: 3000, // Show for 3 seconds
            close: true,
            gravity: "top",
            position: "center",
            className: "toast-message-captcha",
            style: {
                background: background,
                width: "400px",
                textAlign: "center",
                whiteSpace: "normal",
                wordWrap: "break-word",
                borderRadius: "10px",
                padding: "12px",
            },
        }).showToast();
    }

    // CAPTCHA validation
    function validateCaptcha() {
        var response = grecaptcha.getResponse();
        if (response.length === 0) {
            showNotification(
                "⚠️ Please complete the CAPTCHA.",
                "linear-gradient(to right, #ff5f6d, #ffc371)"
            );
            return false;
        }
        return true;
    }

    // Attach event listener when DOM is fully loaded
    $(document).ready(function () {
        var form = $(".oe_login_form");
        var submitButton = form.find("button[type='submit']");

        if (form.length) {
            form.on("submit", function (event) {
                submitButton.prop("disabled", true).html('<i class="fa fa-spinner fa-spin"></i> Logging in...');

                if (!validateCaptcha()) {
                    event.preventDefault(); // Prevent form submission
                    submitButton.prop("disabled", false).html("Log in");
                }
            });
        }
    });
});
