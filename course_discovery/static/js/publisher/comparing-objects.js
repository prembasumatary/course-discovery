$(document).on('click', '.btn-show-changes', function (e) {

    if ($(this).hasClass('show')){
        $('.field-container').each(function () {
            showDiff($(this).find('span.object'), $(this).find('span.history-object'), $(this).find('span.show-diff'));
        });
        $(this).text(gettext('Hide changes'));
        $(this).removeClass('show');
    } else {
        $('.history-object').show();
        $('.show-diff').hide();
        $(this).text(gettext('Show changes'));
        $(this).addClass('show');

    }
});

function getComparableText(object) {
    if ($(object).find('.dont-compare').length > 0) {
        return "";
    } else {
        return object.text().trim()
    }
}

var dmp = new diff_match_patch();
dmp.Diff_EditCost = 8;
function showDiff($object, $historyObject, $outputDiv) {
    var currentText = $($.parseHTML($object.text())).text().trim(),
        historyText = getComparableText($historyObject),
        diff;

    diff = dmp.diff_main(historyText, currentText);
    dmp.diff_cleanupEfficiency(diff);
    $outputDiv.html(dmp.diff_prettyHtml(diff));
    $historyObject.hide();
    $outputDiv.show();
}

function showDiffCourseDetails(currentObject, historyObject, $outputDiv) {
    var d = dmp.diff_main(currentObject, historyObject);
    dmp.diff_cleanupEfficiency(d);
    $outputDiv.html(dmp.diff_prettyHtml(d));
    $outputDiv.show();
}

