function dropdownUpdate(dropdown, selectedElement) {
    if (!selectedElement.hasClass('dropdown-item') && !selectedElement.hasClass('colored-dropdown-item'))
        return;

    $('.active', dropdown).removeClass('active');

    // add class "active" to item and change ".dropdown-toggle" text and color
    let bgColor = selectedElement.addClass('active').css('background-color');
    $('.dropdown-toggle', dropdown)
        .text(selectedElement.text())
        .css({
            'color': selectedElement.css('color'),
            'background-color': bgColor,
            'border-color': bgColor
        });

    $('input[type="hidden"]', dropdown).val(selectedElement.val());
}