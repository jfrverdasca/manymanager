$(document).ready(function () {
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
        dropdownStateUpdate(dropdown, $(`.color-dropdown-item:contains(${category}):first`));

        expensesCategoryBalanceTablesUpdate();
        spentByCategoryChartUpdate();

    }

    function expensesCategoryBalanceTablesUpdate() {
        let fromDate = $('#fromDate').val();
        let toDate = $('#toDate').val();
        let categoryId = $('#categoryDropdownValue').val();

        $.get(`/expenses-categories-balance-tables/${fromDate}/${toDate}/${categoryId}`, function (response) {
            $('#expensesTableArea, #categoriesBalanceTableArea').empty();
            $('#expensesTableLengthArea, #expensesTablePaginationArea, #categoriesBalanceTablePaginationArea').empty()

            let parsedResponse = $(response);
            parsedResponse.filter('#expensesTable').appendTo('#expensesTableArea');
            parsedResponse.filter('#categoriesBalanceTable').appendTo('#categoriesBalanceTableArea');

            let expensesTable = $('#expensesTable').DataTable({
                lengthChange: true,
                lengthMenu: [[25, 50, 100, -1], [25, 50, 100, 'All']],
                order: [[2, 'desc']],
                searching: true,
                info: false,
                sDom: 'tpl',
                oLanguage: {sLengthMenu: '_MENU_'},
                initComplete: (settings, json) => {
                    $('#expensesTable_length').appendTo('#expensesTableLengthArea');
                    $('#expensesTable_paginate').addClass('btn-sm p-0').appendTo('#expensesTablePaginationArea');
                    $('#expensesTablePaginationArea .pagination').addClass('mb-0');
                }
            }).on('draw.dt', function () {
                $('#expensesTablePaginationArea .pagination').addClass('mb-0');
            });

            $('#expensesTableSearch').keyup(function () {
                expensesTable.search($(this).val()).draw();
            });

            let categoriesBalanceTable = $('#categoriesBalanceTable').DataTable({
                pageLength: 5,
                lengthChange: false,
                searching: true,
                info: false,
                sDom: 'tpl',
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

        }).fail(function (xhr, status, error) {
            console.log(status, error, xhr.responseText);
        });
    }

    function favoritesListUpdate() {
        $.get('/favorites-list', function (response) {
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

        favoritesListUpdate();
        quickHistoryChartUpdate();
        expensesCategoryBalanceTablesUpdate();
        spentByCategoryChartUpdate();
    });

    $(document).on('hide.bs.dropdown', '.dropdown:not(header .dropdown)', function (e) {
        let target = $(e.clickEvent.target, this);
        dropdownStateUpdate(this, target);

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
    });

    $('#modalContentArea').change(function () {
        $('#date').datepicker({dateFormat: 'dd-mm-yy'});

        let categoryId= $('input[name="category"]', this).val();
        if (categoryId !== '0')
            dropdownStateUpdate($('.dropdown', this), $(`.color-dropdown-item[value="${categoryId}"]`, this));
    });

    $('#modal').on('post.success', function () {
        favoritesListUpdate();
        quickHistoryChartUpdate();
        expensesCategoryBalanceTablesUpdate();
        spentByCategoryChartUpdate();
    });
});