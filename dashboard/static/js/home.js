$(document).ready(function () {
    // charts
    let quickHistoryChartMonths = $('#quickHistoryChartDropdown').find('.dropdown-item.active').val();

    let spentByCategoryChart = new Chart($('#spentByCategoryChart'), {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            cutoutPercentage: 60,
            aspectRatio: 1.5,
            legend: {display: false}
        }
    });
    
    let quickHistoryChart = new Chart($('#quickHistoryChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            scales: {
                yAxes: [{
                    ticks: {min: 0}
                }]
            },
            legend: {
                onClick: function (event, legendItem) {
                    quickHistoryChart.getDatasetMeta(legendItem.datasetIndex).hidden = !legendItem.hidden;
                    quickHistoryChart.update();
                    
                    $('#spentAverage').text(spentAverageVisibleDatasets());
                }
            },
            onClick: quickHistoryChartClick
        }
    });

    // tables
    let categoriesBalanceTable = $('#categoriesBalanceTable').DataTable({
        pageLength: 5,
        lengthChange: false,
        order: [[3, 'asc']],
        searching: true,
        info: false,
        sDom: 'tpl',
        processing: true,
        serverSide: true,
        deferLoading: false,
        columnDefs: [{
            targets: 0,
            data: null,
            render: function (data, type, row, meta) {
                return `<span style=\"color: ${row[0].color}\">${row[0].name}</span>`
            }
        }, {
            targets: 2,
            data: null,
            render: function (data, type, row, meta) {
                return (row[2] < 0) ? `<span class=\"text-danger\">${row[2]}</span>` :
                    `<span class=\"text-primary\">${row[2]}</span>`
            }
        }, {
            targets: 3,
            data: null,
            render: function (data, type, row, meta) {
                return `<span class=\"text-danger\">${row[3]}</span>`
            }
        }],
        initComplete: (settings, json) => {
            $('#categoriesBalanceTable_paginate').addClass('btn-sm p-0').appendTo('#categoriesBalanceTablePaginationArea');
            $('#categoriesBalanceTablePaginationArea .pagination').addClass('mb-0');
        }

    }).on('draw.dt', function () {
        $('#categoriesBalanceTablePaginationArea .pagination').addClass('mb-0');
    });

    $('#categoriesBalanceTableSearch').keyup(function () {
        categoriesBalanceTable.search($(this).val()).draw();
    });

    let expensesTable = $('#expensesTable').DataTable({
        columns: [
            {data: 'description'},
            {data: 'category'},
            {data: 'timestamp'},
            {data: 'value'},
            {data: 'id'},
            {data: 'shared'}
        ],
        lengthChange: true,
        lengthMenu: [[25, 50, 100, -1], [25, 50, 100, 'All']],
        order: [[2, 'desc']],
        searching: true,
        info: false,
        sDom: 'tpl',
        oLanguage: {sLengthMenu: '_MENU_'},
        processing: true,
        serverSide: true,
        deferLoading: false,
        columnDefs: [{
            targets: 1,
            render: function (data, type, row, meta) {
                return `<span style=\"color: ${row.category.color}\">${row.category.name}</span>`
            }
        }, {
            targets: 4,
            searchable: false,
            orderable: false,
            render: function (data, type, row, meta) {
                return `<button class="btn btn-sm text-primary text-decoration-none shadow-none p-0" 
                        type="button" data-bs-toggle="modal" data-bs-target="#modal" 
                        value="popups/expense/${row.id}/update">
                            <i class="bi-pencil" style="font-size: 18px;"></i>
                        </button>
                        <button class="btn btn-sm text-danger text-decoration-none shadow-none p-0 ms-2" 
                        type="button" data-bs-toggle="modal" data-bs-target="#modal" 
                        value="popups/expense/${row.id}/delete">
                            <i class="bi-trash" style="font-size: 18px;"></i>
                        </button>`
            }
        }, {
            targets: 5,
            searchable: false,
            orderable: false,
            render: function (data, type, row, meta) {
                if (row.shared)
                    return `<span>
                                <i class="bi-share" style="font-size: 18px;"></i>
                            </span>`

                return null;
            }
        }],
        initComplete: (settings, json) => {
            $('#expensesTable_length').appendTo('#expensesTableLengthArea');
            $('#expensesTable_paginate').addClass('btn-sm p-0').appendTo('#expensesTablePaginationArea');
            $('#expensesTablePaginationArea .pagination').addClass('mb-0');
        },

    }).on('draw.dt', function () {
        $('#expensesTablePaginationArea .pagination').addClass('mb-0');
    });

    $('#expensesTableSearch').keyup(function () {
        expensesTable.search($(this).val()).draw();
    });

    // others
    function expensesCategoryBalanceTablesUpdate() {
        let fromDate = $('#fromDate').val();
        let toDate = $('#toDate').val();
        let categoryId = $('#categoryDropdownValue').val();

        categoriesBalanceTable.ajax.url(`../categories_balance_table/${fromDate}/${toDate}/${categoryId}/`).draw();
        expensesTable.ajax.url(`../expenses_table/${fromDate}/${toDate}/${categoryId}/`).draw();
    }

    function spentAverageVisibleDatasets() {
        let total = 0;
        let datasetsWithData = Array();

        $(quickHistoryChart.data.datasets).each(function (i, e) {
            if (quickHistoryChart.getDatasetMeta(i).hidden)
                return;

            e.data.reduce(function (_, value, i) {
                if (value === 0)
                    return;

                datasetsWithData[i] = true;
                total += value
            }, 0);
        });
        return total === 0 ? 0 : (total / Object.keys(datasetsWithData).length).toFixed(2);
    }

    function quickHistoryChartClick(event, array) {
        // there is another way to get the month number using Date object, but let's keep it simple
        const MONTHS = {'January': 1,
                    'February': 2,
                    'March': 3,
                    'April': 4,
                    'May': 5,
                    'June': 6,
                    'July': 7,
                    'August': 8,
                    'September': 9,
                    'October': 10,
                    'November': 11,
                    'December': 12};

        let element = quickHistoryChart.getElementAtEvent(event);
        if (!element.length)
            return;

        element = element[0]

        let category = quickHistoryChart.data.datasets[element._datasetIndex].label
        let monthNumber = MONTHS[quickHistoryChart.data.labels[element._index]];
        let year = new Date().getFullYear();
        let lastMonthDay = new Date(year, monthNumber, 0).getDate();

        // calculate selected year
        for (let i = quickHistoryChart.data.labels.length - 1; i >= element._index; i--) {
            if (quickHistoryChart.data.labels[i] === 'December')
                year -= 1;
        }

        // update interface elements
        $('#fromDate').datepicker('setDate', `1-${monthNumber}-${year}`);
        $('#toDate').datepicker('setDate', `${lastMonthDay}-${monthNumber}-${year}`);

        let dropdown = $('#categoryDropdown');
        dropdownUpdate(dropdown, $(`.colored-dropdown-item:contains(${category}):first`));

        expensesCategoryBalanceTablesUpdate();
        spentByCategoryChartUpdate();
    }

    function alertsListUpdate() {
        $.get('/ajax/alerts-list', function (response) {
            $('#alertsListArea').html(response);

            let alertsHeight = 0
            $('#alertsListArea .card').each(function (i, e) {
                alertsHeight += $(e).height();

                if (i === 1) {
                    $('#alertsListArea').parent().height(alertsHeight);
                    return false;
                }
            });
        });
    }

    function favoritesListUpdate() {
        $.get('/ajax/favorites-list', function (response) {
            $('#favoritesListArea').html(response);

            $('#favoritesList').sortable().disableSelection().on('sortupdate', function (e, ui) {
                let orderedItem = $(ui.item);
                $.ajax({
                    url: `/favorite/${orderedItem.val()}`,
                    method: 'PATCH',
                    headers: {'Content-Type': 'application/json',
                              'X-CSRF-Token': $('meta[name="csrf"]').attr('content')},
                    data: JSON.stringify({'sort': orderedItem.index()}),
                    error: (xhr, status, error) => {console.log(status, error)},
                    success: () => favoritesListUpdate()
                });
            });
        }).fail(function (xhr, status, error) {
            console.log(status, error, xhr.responseText);
        });
    }

    function quickHistoryChartUpdate() {
        $.get(`/quick-history-chart/${quickHistoryChartMonths}`, function (response) {
            quickHistoryChart.data = response;
            quickHistoryChart.update();

        }).done(function () {
            $('#spentAverage').text(spentAverageVisibleDatasets());

        }).fail(function (xhr, status, error) {
            console.log(status, error, xhr.responseText);
        });
    }

    function spentByCategoryChartUpdate() {
        let fromDate = $('#fromDate').val();
        let toDate = $('#toDate').val();
        let categoryId = $('#categoryDropdownValue').val();

        $.get(`/spent-by-category-chart/${fromDate}/${toDate}/${categoryId}`, function (response) {
            spentByCategoryChart.data = response.chart_data
            spentByCategoryChart.update();

            $('#totalSpent').text(response.total)
        })
    }

    $(function () {
        $('#fromDate, #toDate').datepicker({dateFormat: 'dd-mm-yy'}).change(function () {
            expensesCategoryBalanceTablesUpdate();
            spentByCategoryChartUpdate();
        });

        alertsListUpdate();
        favoritesListUpdate();
        quickHistoryChartUpdate();
        expensesCategoryBalanceTablesUpdate();
        spentByCategoryChartUpdate();
    });

    $(document).on('hide.bs.dropdown', '.dropdown:not(header .dropdown)', function (e) {
        let target = $(e.clickEvent.target, this);
        dropdownUpdate(this, target);

        switch ($(this).attr('id')) {
            case 'quickHistoryChartDropdown':
                quickHistoryChartMonths = target.val();
                quickHistoryChartUpdate();
                break;

            case 'categoryDropdown':
                expensesCategoryBalanceTablesUpdate();
                spentByCategoryChartUpdate();
                break;
        }
    }).on('click', '#favoritesList li', function () {
        $.ajax({
            url: '/favorite-replica',
            method: 'POST',
            headers: {'Content-Type': 'application/json',
                      'X-CSRF-Token': $('meta[name="csrf"]').attr('content')},
            data: JSON.stringify({'id': $(this).val()}),
            error: (xhr, status, error) => {console.log(status, error)},
            success: () => {
                quickHistoryChartUpdate();
                expensesCategoryBalanceTablesUpdate();
                spentByCategoryChartUpdate();
            }
        });
    }).on('click', '#closeAlert', function () {
        $.ajax({
            url: `/seen-alert/${$(this).val()}`,
            method: 'POST',
            headers: {'Content-Type': 'application/json',
                      'X-CSRF-Token': $('meta[name="csrf"]').attr('content')},
            error: (xhr, status, error) => {console.log(status, error)},
            success: () => {
                alertsListUpdate();
            }
        });
    });

    $('#modalContentArea').change(function () {
        let categoryId= $('input[name="category"]', this).val();
        if (categoryId !== '0')
            dropdownUpdate($('.dropdown', this), $(`.colored-dropdown-item[value="${categoryId}"]`, this));
    });

    $('#modal').on('post.success', function () {
        alertsListUpdate();
        favoritesListUpdate();
        quickHistoryChartUpdate();
        expensesCategoryBalanceTablesUpdate();
        spentByCategoryChartUpdate();
    });
});