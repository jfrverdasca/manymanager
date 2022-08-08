$(document).ready(function () {
    // tables
    let categoriesTable = $('#categoriesTable').DataTable({
        pageLength: 10,
        lengthChange: false,
        order: [[0, 'asc']],
        searching: true,
        info: false,
        sDom: 'tpl',
        processing: true,
        serverSide: true,
        deferLoading: 0,
        ajax: '../categories_table/',
        columnDefs: [{
            targets: 0,
            data: null,
            render: function (data, type, row, meta) {
                return `<span style=\"color: ${data[0].color}\">${data[0].name}</span>`
            }
        }, {
            targets: 2,
            data: null,
            render: function (data, type, row, meta) {
                return `<button class="btn btn-sm text-primary text-decoration-none shadow-none p-0" 
                        type="button" data-bs-toggle="modal" data-bs-target="#modal" 
                        value="/category/${data[2]}/update">
                            <i class="bi-pencil" style="font-size: 18px;"></i>
                        </button>
                        <button class="btn btn-sm text-danger text-decoration-none shadow-none p-0 ms-2" 
                        type="button" data-bs-toggle="modal" data-bs-target="#modal" 
                        value="/category/${data[2]}/delete">
                            <i class="bi-trash" style="font-size: 18px;"></i>
                        </button>`
            }
        }],
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
        order: [[3, 'asc']],
        searching: true,
        info: false,
        sDom: 'tpl',
        processing: true,
        serverSide: true,
        deferLoading: 0,
        ajax: '../favorites_table',
        columnDefs: [{
            targets: 0,
            data: null,
            render: function (data, type, row, meta) {
                return `<span style=\"color: ${data[0].color}\">${data[0].name}</span>`
            }
        }, {
            targets: 2,
            data: null,
            render: function (data, type, row, meta) {
                return `<button class="btn btn-sm text-danger text-decoration-none shadow-none p-0" type="button" 
                        data-bs-toggle="modal" data-bs-target="#modal" 
                        value="/favorite/${data[2]}/remove">
                            <i class="bi-bookmark-star" style="font-size: 18px;"></i>
                        </button>`
            }
        }, {
            targets: 3,
            data: null,
            createdCell: function (td, cellData, rowData, row, col) {
                $(td).attr("hidden",true);
            }
        }],
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

    function categoriesFavoritesTablesUpdate() {
        categoriesTable.draw();
        favoritesTable.draw();
    }

    $(function () {
        categoriesFavoritesTablesUpdate();
    });

    $('#modal').on('post.success', function () {
        categoriesFavoritesTablesUpdate();
    });
});