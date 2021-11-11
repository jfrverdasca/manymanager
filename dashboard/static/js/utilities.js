function modal(contentUrl, onContentLoadedCallback, onPostSuccessCallback) {
    function onModalResponse(response) {
        let content = $('#modal_content_area').html(response);

        if(onContentLoadedCallback)
            onContentLoadedCallback(content);

        $('#modal_content_area form').submit(function (e) {
            $.post(contentUrl, $(this).serialize(), function (response) {
                onModalResponse(response);

            }).done(function(data, status, xqr) {
                if (data || xqr.status !== 200)
                    return;

                $('#modal').modal('hide');
                onPostSuccessCallback(data);

            }).fail(function (xhr, status, error) {
                console.log(status, error);
            });
            e.preventDefault();
        });
    }

    $.get(contentUrl, function (response) {
        onModalResponse(response);
    }).done(
        $('#modal').modal('show')

    ).fail(function (xhr, status, error) {
        console.log(status, error);
    });
}
