function dropdownStateUpdate(dropdown, element) {
    if (!element.hasClass('dropdown-item') && !element.hasClass('color-dropdown-item'))
        return;

    let value = element.val();
    if (!value)
        return;

    $('input[type="hidden"]', dropdown).val(value);
    $('.dropdown-item.active, .color-dropdown-item.active', dropdown).removeClass('active');
    $(`.dropdown-item[value="${value}"], .color-dropdown-item[value="${value}"]`, dropdown).addClass('active');
    $('.dropdown-toggle', dropdown).css({
            'color': '#fff',
            'background-color': element.css('background-color'),
            'border-color': element.css('background-color')})
        .text(element.text());
}
