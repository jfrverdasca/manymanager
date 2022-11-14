$(document).ready(function () {
    let modalUrl;

    $('#modal').on('show.bs.modal', (e) => {
        modalUrl = $(e.relatedTarget).val();

        // perform request
        $.get(modalUrl).done((data) => {
            // add popover to submit control
            $('#modalContentArea').html(data).change();

            $('#modalContentArea, #loading').toggle();

        }).fail((error) => {
            $('#status').text(error.status);
            $('#error').text(error.responseText);

            $('#loading, #loadingFailed').toggle();
        });

    }).on('hidden.bs.modal', (e) => {
        $('#modalContentArea, #loadingFailed').hide();
        $('#loading').show();
    });

    $(document).on('submit', '#modalContentArea form', function (e) {
        $.post(modalUrl, $(this).serialize()).done((data) => {
            if (!data)
                $('#modal').modal('hide').trigger('post.success');

            else
                $('#modalContentArea').html(data);

        }).fail((error) => {
            // add required attributes for popover
            new bootstrap.Popover($('#submit'), {
                container: 'body',
                placement: 'right',
                html: true,
                trigger: 'focus',
                title: 'Request failed!',
                content:
                    `<div class="row mb-3">
                        <div class="col-12">
                            The request cannot be satisfied. Please try again.
                        </div>        
                    </div>
                    <div class="row">
                       <div class="col-12 text-center">
                            <small class="d-block">
                                <b>Error:</b> ${error.status}
                            </small>
                            <small class="d-block">
                                <b>Status:</b> ${error.responseText}
                            </small>
                        </div>
                    </div>`,
                template:
                    `<div class="popover shadow-sm" role="tooltip">
                        <div class="popover-arrow"></div>
                        <h3 class="popover-header bg-danger text-white"></h3>
                        <div class="popover-body"></div>
                    </div>`
            }).show();
        });

        e.preventDefault();

    }).on('hidden.bs.popover', (e) => {
        let popover = bootstrap.Popover.getInstance($('#submit'));
        if (popover)
            popover.dispose();
    });
});