var _ = require('underscore');
var Pikaday = require('pikaday');

require('js-cookie');
require('moment');
require('datatables');


require('./publisher.js');
require('./views/navbar.js');
require('./seat-type-change.js');
require('./tabs.js');
require('./utils.js');


$(document).ready(function () {
    _.each($('.add-pikaday'), function (el) {
        if (el.getAttribute('datepicker-initialized') !== 'true') {
            new Pikaday({
                field: el,
                format: 'YYYY-MM-DD',
                defaultDate: $(el).val(),
                setDefaultDate: true,
                showTime: false,
                use24hour: false,
                autoClose: true
            });
            el.setAttribute('datepicker-initialized', 'true');
        }
    });
});
