$(document).ready(function () {
    function categoriesFavoritesTablesUpdate() {
        $.get('/categories_favorites_tables', function (response) {
            $('#alertsTableArea, #categoriesTableArea, #favoritesTableArea, #sharesTableArea').empty();
            $('#categoriesTablePaginationArea, #favoritesTablePaginationArea').empty();

            let parsedResponse = $(response);
            parsedResponse.filter('#alertsTable').appendTo('#alertsTableArea');
            parsedResponse.filter('#categoriesTable').appendTo('#categoriesTableArea');
            parsedResponse.filter('#favoritesTable').appendTo('#favoritesTableArea');
            parsedResponse.filter('#sharesTable').appendTo('#sharesTableArea');

            let categoriesTable = $('#categoriesTable').DataTable({
                pageLength: 10,
                lengthChange: false,
                order: [[2, 'desc']],
                searching: true,
                info: false,
                sDom: 'tpl',
                initComplete: (settings, json) => {
                    $('#categoriesTable_length').appendTo('#categoriesTableLengthArea');
                    $('#categoriesTable_paginate').addClass('btn-sm p-0').appendTo('#categoriesTablePaginationArea');
                    $('#categoriesTablePaginationArea .pagination').addClass('mb-0');
                }
            }).on('draw.dt', function () {
                $('#categoriesTablePaginationArea .pagination').addClass('mb-0');
            });

            $('#categoriesTableSearch').keyup(function () {
                categoriesTable.search($(this).val()).draw();
            });

            let favoritesTable = $('#favoritesTable').DataTable({
                pageLength: 10,
                lengthChange: false,
                order: [[2, 'desc']],
                searching: true,
                info: false,
                sDom: 'tpl',
                initComplete: (settings, json) => {
                    $('#favoritesTable_length').appendTo('#favoritesTableLengthArea');
                    $('#favoritesTable_paginate').addClass('btn-sm p-0').appendTo('#favoritesTablePaginationArea');
                    $('#favoritesTablePaginationArea .pagination').addClass('mb-0');
                }
            }).on('draw.dt', function () {
                $('#favoritesTablePaginationArea .pagination').addClass('mb-0');
            });

            $('#favoritesTableSearch').keyup(function () {
                favoritesTable.search($(this).val()).draw();
            });

        }).fail(function (xhr, status, error) {
            console.log(status, error, xhr.responseText);
        });
    }

    $(function () {
        categoriesFavoritesTablesUpdate();
    });

    $('#modal').on('post.success', function () {
        categoriesFavoritesTablesUpdate();
    });
});