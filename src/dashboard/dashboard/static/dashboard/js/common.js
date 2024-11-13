/**
 * Common JavaScript used in dashboard project
 */

'use strict';

const app = window.app = {
    /** ### CALL FUNCTIONS ###*/
    init: function () {
        this.languageSwitcher();
    },

    /** ### FUNCTIONS ###*/

    /**
     * Language switcher
     * Sets django_language cookie, with the current language choice chosen by the user.
     */
    languageSwitcher: function () {
        const language_selectors = document.querySelectorAll(".fr-translate__language")

        language_selectors.forEach(el => el.addEventListener("click", event => {
            document.cookie = "django_language=" + el.lang + ";Path=\"/django-dsfr\";SameSite=Strict"
            window.location.reload()
        }));
    }
}


/**
 *
 * Wait for DOM ready and init() the app
 *
 */
document.onreadystatechange = function () {
    if (document.readyState === "interactive") {
        app.init();
    }
}
