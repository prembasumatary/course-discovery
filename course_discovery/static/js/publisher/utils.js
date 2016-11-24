


function interpolateString(formatString, parameters) {
    return formatString.replace(/{\w+}/g,
        function(parameter) {
            var parameterName = parameter.slice(1,-1);
            return String(parameters[parameterName]);
        });
}

function alertTimeout(wait, elementName) {
    var element = elementName || ".alert-messages";
    setTimeout(function(){
        $(element).hide();
    }, wait);
}
