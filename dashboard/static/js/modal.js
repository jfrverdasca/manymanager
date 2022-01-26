$(document).ready(function () {
    $('#modal').on('show.bs.modal', function (e) {
        function onModalResponse(url, component, response) {
            $('#modalContentArea').html(response).change();  // raise change event

            $('#modalContentArea form').submit(function (e) {
                $.post(url, $(this).serialize(), function (response) {
                    onModalResponse(url, component, response);

                }).done(function (data, status, xhr) {
                    if (data || xhr.status !== 200)
                        return;

                    component
                        .modal('hide')
                        .trigger('post.success', url);

                }).fail(function (xhr, status, error) {
                    console.log(status, error, xhr.responseText);
                });

                e.preventDefault();
            })
        }

        let url = $(e.relatedTarget).val();
        let component = $(this);

        $.get(url, function (response) {
            onModalResponse(url, component, response)

        }).done(function () {
            $('#modalContentArea, #loadingAnimation').toggle();

        }).fail(function (xhr, status, error) {
            console.log(status, error, xhr.responseText);
        });

    }).on('hidden.bs.modal', function (e) {
        $('#modalContentArea').empty().hide();
        $('#loadingAnimation').show();
    });
});