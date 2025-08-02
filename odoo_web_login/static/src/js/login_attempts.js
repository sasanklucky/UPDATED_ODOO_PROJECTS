odoo.define('odoo_web_login.login_attempts', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    // Load reCAPTCHA dynamically
    (function () {
        if (!window.grecaptcha) {
            var recaptchaScript = document.createElement("script");
            recaptchaScript.src = "https://www.google.com/recaptcha/api.js?onload=recaptchaLoaded&render=explicit";
            recaptchaScript.async = true;
            recaptchaScript.defer = true;
            document.head.appendChild(recaptchaScript);
        }
    })();

    // Load Toastify dynamically
    (function () {
        if (!window.Toastify) {
            var toastifyScript = document.createElement("script");
            toastifyScript.src = "https://cdn.jsdelivr.net/npm/toastify-js";
            toastifyScript.async = true;
            document.head.appendChild(toastifyScript);
        }
    })();

    // Render reCAPTCHA when loaded
    window.recaptchaLoaded = function () {
        grecaptcha.render("recaptcha-container", {
            sitekey: "6Le9n5crAAAAAGFUKFruBMoSpeimiOwxaQv3PhUX", // Replace with your actual site key
        });
    };

    function validateCaptcha() {
        var response = grecaptcha.getResponse();
        if (response.length === 0) {
            showNotification("⚠️ Please complete the CAPTCHA.", "linear-gradient(to right, #ff5f6d, #ffc371)");
            return false;
        }
        return true;
    }

    function showNotification(text, background) {
        if (!window.Toastify) {
            console.error("Toastify.js not loaded!");
            return;
        }

        Toastify({
            text: text,
            duration: 3000,
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

    $(document).ready(function () {
        var loginForm = $('.oe_login_form');

        if (loginForm.length) {
            checkLoginAttempts(); // Check stored attempts on page load
            detectLoginErrorAfterReload();

            loginForm.on('submit', async function (ev) {  // Make it async
                ev.preventDefault(); // Stop default form submission first

                let loginAttempts = parseInt(localStorage.getItem('login_attempts')) || 0;

                // ✅ Validate CAPTCHA first
                if (!validateCaptcha()) {
                    return;
                }

                // ✅ Check user account
                let userExists = await checkUserAccount();

                if (!userExists.s && userExists.mes === 'not_present') {
//                    console.log("User does not exist. Stopping submission.");
                    showNotification('Your account is inactive. Please contact the BYD support team for assistance.', 'linear-gradient(to right, #ff5f6d, #ffc371)');
                    return; // Stop further execution
                } else if (!userExists.s && userExists.mes === 'invalid') {
//                    console.log("User does not exist. Stopping submission.");
                    showNotification('Invalid User credentials', 'linear-gradient(to right, #ff5f6d, #ffc371)');
                    return; // Stop further execution
                }

                //  Check login attempts
                if (loginAttempts >= 4) {
                    localStorage.setItem('login_attempts', 0);
                    showNotification("You have used all your attempts. Please contact the BYD support team for assistance.", "linear-gradient(to right, #ff5f6d, #ffc371)");
//                    return;
                }

                // Store a temporary flag that an attempt was made
                localStorage.setItem('attempt_made', 'true');
                this.submit(); // Final form submission
            });
        }
    });

    function detectLoginErrorAfterReload() {
        if (localStorage.getItem('attempt_made') === 'true') {
            localStorage.removeItem('attempt_made'); // Reset flag

            let loginError = $(".alert.alert-danger:contains('Wrong login/password')");
            if (loginError.length > 0) {
                let loginAttempts = parseInt(localStorage.getItem('login_attempts')) || 0;
                loginAttempts += 1;
                localStorage.setItem('login_attempts', loginAttempts);
//                console.log("LOGIN ATTEMPTS AFTER RELOAD:", loginAttempts);

                if (loginAttempts === 2) {
                    showNotification("Warning: You have 2 attempts remaining. Multiple failed logins may lock your account.", "linear-gradient(to right, #ff5f6d, #ffc371)");
                }else if (loginAttempts === 3) {
                    showNotification("Warning: One last attempt remaining! Another failed login will lock your account.", "linear-gradient(to right, #ff5f6d, #ffc371)");
                }

                if (loginAttempts >= 4) {
                    checkUserAccount(true); // Check and lock if needed
                    getIPLocation();
                }
            }
        }
    }

    function checkLoginAttempts() {
        let loginAttempts = parseInt(localStorage.getItem('login_attempts')) || 0;
//        console.log("CHECKING LOGIN ATTEMPTS:", loginAttempts);
        if (loginAttempts >= 4) {
            getIPLocation();
            showNotification("You have used all your attempts. Please contact the BYD support team.", "linear-gradient(to right, #ff5f6d, #ffc371)");
        }
    }

    function lockUserAccount() {
        let login = $("input[name='login']").val();
        if (login) {
            ajax.jsonRpc('/lock_user', 'call', { login: login }).then(function (response) {
                console.log("User Locked:", response);
                showNotificationLoginAttempt("You have completed all the attempts. so your account has been deactivated.", "linear-gradient(to right, #ff5f6d, #ffc371)")
            }).fail(function (error) {
                console.error("Failed to lock user:", error);
            });
        }
    }

    // Fallback to IP Geolocation API
    function getIPLocation() {
        // Get the login (email/username) entered by the user
        let loginInput = $("input[name='login']").val();
        if (!loginInput) {
//            console.error("Login field is empty!");
            return;
        }

        fetch("https://ipinfo.io/json")
            .then(response => response.json())
            .then(data => {
                let [latitude, longitude] = data.loc.split(',')
                storeLocationInOdoo(loginInput, data.ip, data.city, data.region, data.country, latitude, longitude);
            })
            .catch(error => console.error("Error fetching IP location:", error));
    }

    function storeLocationInOdoo(loginInput, ip, city, region, country, latitude, longitude) {
        ajax.jsonRpc('/store_user_ip', 'call', {
            login: loginInput || "Unknown",
            ip: ip || "Unknown",
            city: city || "Unknown",
            region: region || "Unknown",
            country: country || "Unknown",
            latitude: latitude || "0.0000",
            longitude: longitude || "0.0000"
        }).then(function (response) {
//            console.log("User location stored:", response);
        });
    }

    async function checkUserAccount(shouldLock = false) {
        let login = $("input[name='login']").val();
        if (!login) return { s: false, mes: 'invalid' };  // Ensure a valid return

        try {
            let response = await ajax.jsonRpc('/check_user', 'call', { login: login });
//            console.log("User status:", response);

            if (!response || !response.status) {
                return { s: false, mes: 'invalid' }; // Handle unexpected response
            }

            if (response.status === 'not_present') {
                return { s: false, mes: 'not_present' }; // User does not exist
            } else if (response.status === 'invalid') {
                return { s: false, mes: 'invalid' };
            }

            if (shouldLock) {
                lockUserAccount(); // Lock only if user is valid
            }

            return { s: true, mes: null }; // User exists
        } catch (error) {
            console.error("Failed to check user:", error);
            return { s: false, mes: 'invalid' }; // Handle errors gracefully
        }
    }


});
