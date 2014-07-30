var vote_id;
var client;
var sub_id;
var all_seq = [];
var choice_data = [];
var choice_content = [];
var max_count = 0;
var voter_count = 0;
var plot;
var vote_server;

function msg_handler(message) {
    var seq = message.headers.seq;
    if ($.inArray(seq, all_seq) < 0) {
        var data = $.parseJSON(message.body);
        var max = 0;
        if (data.vote_id == vote_id) {
            $.each(data.selections, function(i, x) {
                choice_data[x].data[0][1]++;
                var v = choice_data[x].data[0][1];
                if (max < v) max = v;
            });
            if (max >= max_count) {
                max_count += 20;
                plot.getOptions().yaxes[0].max = max_count;
                plot.setupGrid();
            }
            plot.setData(choice_data);
            plot.draw();
            $('#voter_count').text(++voter_count);
        }
        all_seq.push(seq);
    }
}

function subscribe(vid) {
    if (window.WebSocket) {
        client = Stomp.client(vote_server.url);
        sub_id = 'ws' + vid;
        client.connect(
            vote_server.user,
            vote_server.password,
            function(frame) {
                client.subscribe('/dsub/vote' + vid, msg_handler, {
                    id: sub_id,
                    //persistent: true,
                    browser: true,
                    'browser-end': false,
                    'include-seq': 'seq',
                    'from-seq': 0
                });
            });
    }
}

function prepare(vid, vote_data, finished) {
    vote_id = vid;
    var max = 0;
    var data = $.parseJSON(vote_data);
    vote_server = data.server;
    choice_data = $.map(data.choices, function(x, i) {
        choice_content.push(x[0]);
        n = x[1];
        if (max < n) max = n;
        return { data: [[i + 1, n]] };
    });
    max_count = Math.floor((max + 9) / 10) * 10 + 20;
    plot();
    if (finished) {
    } else {
        subscribe(vid);
    }
}

$(document).unload(function() {
    if (client)
        client.unsubscribe(sub_id);
});

function plot() {
    var options = {
        hack_3d_grid: true,
        series: {
            stack: true,
            bars: {
                show: true,
                fill: 1,
                barWidth: 0.9,
                align: 'center',
                order: 1
            }
        },
        grid: {
            borderWidth: 1,
            minBorderMargin: 20,
            labelMargin: 10,
            backgroundColor: {
                colors: ['#fff', '#e4f4f4']
            },
            hoverable: false,
            mouseActiveRadius: 50,
            margin: {
                top: 8,
                bottom: 20,
                left: 20
            }
        },
        xaxis: {
            ticks: $.map(choice_data, function(x, i) {
                return [[x.data[0][0], choice_content[i]]];
            }),
            rotateTicksFont: 'SimHei',
            rotateTicks: 150
        },
        yaxis: {
            max: max_count,
            ticks: 5,
            tickDecimals: 0
        },
        legend: {
            show: true
        },
        valueLabels: {
            show: true,
            labelFormatter: function(v) {
                return v == 0 ? '' : v;
            }
        }
    };
    plot = $.plot(
        $('#placeholder'),
        // $.map(choice_data, function(x, i) {
        //     return { data: [x] };
        // }),
        choice_data,
        options);
}
