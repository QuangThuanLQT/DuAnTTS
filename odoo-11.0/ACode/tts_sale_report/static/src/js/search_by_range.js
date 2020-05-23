odoo.define('tts_sale_report.pivot', function (require) {
    "use strict";

    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var PivotView = require('web.PivotView');
    var datepicker = require('web.datepicker');
    var GraphView = require('web.GraphView');
    var GraphWidget = require('web.GraphWidget');

    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    PivotView.include({
        render_buttons: function($node) {
            var self = this;
            var ts_context = this.context.tree_search;

            this._super.apply(this, arguments);

            if (self.$search_range && (self.model == 'tts.sale.report' ||self.model == 'tts.product.report')) {
                setTimeout(function () {
                    // $(".sky_select_range_field option[value='total_amount']").remove()
                    $(".sky_select_range_field").addClass('hidden')
                    $(".sky_start_range").addClass('hidden')
                    $(".sky_end_range").addClass('hidden')
                    }, 1000);
            }
        }

    })

    GraphWidget.include({
        display_graph: function () {
            var self = this;
            this._super.apply(this, arguments);

            if (self.context.doanh_so_base_date || self.context.doanh_so_base_week || self.context.doanh_so_base_month) {
                var text_list = self.$el.find('g.nv-y.nv-axis.nvd3-svg g.tick text')
                for ( var i = 0; i < text_list.length; i++ ) {
                    text_list[i].innerHTML = text_list[i].innerHTML.split('.')[0]
                }

                if (self.context.doanh_so_base_date) {
                    var text_list_time = self.$el.find('g.nvd3.nv-wrap.nv-axis g.tick.zero text')
                    for ( var i = 0; i < text_list_time.length; i++ ) {
                        var text_time = text_list_time[i].innerHTML
                        var text_date = text_time.split(' ')
                        if (text_date.length > 1) {
                            text_date = text_date[text_date.length - 1]
                            var text_day = text_time.replace(' ' + text_date,'')
                            text_list_time[i].innerHTML = "     " + text_day
                            if (text_time.indexOf('CN') != -1) {
                                var text = '<text dy=".71em" y="7" transform="rotate(0 0,0)" x="10" style="text-anchor: end; opacity: 1;">'+ text_day +'</text>' +
                                    '<text dy=".71em" y="20" transform="rotate(0 0,0)" x="15" style="text-anchor: end; opacity: 1;">'+ text_date +'</text>'
                            }
                            else {
                                var text = '<text dy=".71em" y="7" transform="rotate(0 0,0)" x="15" style="text-anchor: end; opacity: 1;">'+ text_day +'</text>' +
                                    '<text dy=".71em" y="20" transform="rotate(0 0,0)" x="15" style="text-anchor: end; opacity: 1;">'+ text_date +'</text>'
                            }
                            text_list_time[i].insertAdjacentHTML('afterend',text)
                            text_list_time[i].setAttribute('class',"hidden")
                        }
                    }
                }
                else {
                    if (self.context.doanh_so_base_week || self.context.doanh_so_base_month) {
                        var text_list_time = self.$el.find('g.nvd3.nv-wrap.nv-axis g.tick.zero text')
                        for ( var i = 0; i < text_list_time.length; i++ ) {
                            if (text_list_time[i].innerHTML.split(' ').length > 1) {
                                var text = '<text dy=".71em" y="7" transform="rotate(0 0,0)" x="15" style="text-anchor: end; opacity: 1;">'+ text_list_time[i].innerHTML +'</text>'
                                text_list_time[i].insertAdjacentHTML('afterend',text)
                                text_list_time[i].setAttribute('class',"hidden")
                            }
                        }
                    }
                }

                var text_list = $('g.nvd3.nv-wrap.nv-axis g.nv-axisMaxMin.nv-axisMaxMin-y.nv-axisMax-y text')
                for ( var i = 0; i < text_list.length; i++ ) {
                    text_list[i].innerHTML = 'Tr'
                }
                var legendWrap = $('g.nv-legendWrap')
                for ( var i = 0; i < legendWrap.length; i++ ) {
                     legendWrap[i].classList.value = legendWrap[i].classList.value + " hidden"
                }

                $('button.oe_dashboard_link_change_layout').addClass('hidden')
                setTimeout(function () {
                    var rect_list = self.$el.find('g.nv-groups rect.nv-bar.positive')
                    for ( var i = 0; i < rect_list.length; i++ ) {
                        Number.prototype.format = function(n, x) {
                            var re = '\\d(?=(\\d{' + (x || 3) + '})+' + (n > 0 ? '\\.' : '$') + ')';
                            return this.toFixed(Math.max(0, ~~n)).replace(new RegExp(re, 'g'), '$&,');
                        };
                        // var text = '<text x="' + (parseInt(rect_list[i].getAttribute('y')) + 50) + '" y="' + rect_list[i].getAttribute('x') + '" font-family="Verdana" font-size="55" fill="red">' + rect_list[i].__data__.y + ' tr</text>'
                        var text = '<text x="' + (parseInt(rect_list[i].getAttribute('x')) + ((parseInt(rect_list[i].getAttribute('width')) + 3) / 3)) + '" y="' + (parseInt(rect_list[i].getAttribute('y'))-2) + '" font-family="Verdana" style="font-size: 13px" fill="black" transform="' + rect_list[i].getAttribute('transform') + '">' + rect_list[i].__data__.y.format() + '</text>'
                        rect_list[i].insertAdjacentHTML('afterend',text)
                    }
                }, 1000);
            }
        },
        // display_bar: function() {
        //     var self = this;
        //     var chart = this._super.apply(this, arguments);
        //     var text_list = this.$el.find('g.nv-y.nv-axis.nvd3-svg g.tick text')
        //     for ( var i = 0; i < text_list.length; i++ ) {
        //         text_list[i].innerHTML = text_list[i].innerHTML.split('.')[0] + " tr"
		 //    }
		 //    var text_list = $('g.nvd3.nv-wrap.nv-axis g.nv-axisMaxMin.nv-axisMaxMin-y.nv-axisMax-y text')
        //     for ( var i = 0; i < text_list.length; i++ ) {
			//     text_list[i].innerHTML = ''
		 //    }
		 //    var legendWrap = $('g.nv-legendWrap')
        //     for ( var i = 0; i < legendWrap.length; i++ ) {
			//      legendWrap[i].classList.value = legendWrap[i].classList.value + " hidden"
		 //    }
        //
		 //    $('button.oe_dashboard_link_change_layout').addClass('hidden')
        //
        //     var rect_list = this.$el.find('g.nv-groups rect.nv-bar.positive')
        //     for ( var i = 0; i < rect_list.length; i++ ) {
        //         // var text = '<text x="' + (parseInt(rect_list[i].getAttribute('y')) + 50) + '" y="' + rect_list[i].getAttribute('x') + '" font-family="Verdana" font-size="55" fill="red">' + rect_list[i].__data__.y + ' tr</text>'
        //         var text = '<text x="' + (parseInt(rect_list[i].getAttribute('x'))) + '" y="' + (403 - parseInt(rect_list[i].getAttribute('height'))) + '" font-family="Verdana" font-size="55" fill="red" transform="' + rect_list[i].getAttribute('transform') + '">' + rect_list[i].__data__.y + ' tr</text>'
			//     rect_list[i].insertAdjacentHTML('afterend',text)
		 //    }
        //     return chart
        // },
    })

    GraphView.include({
        render_buttons: function ($node) {
            if ($node) {
                var self = this;
                this._super.apply(this, arguments);
                var a = 1111
            }
        },
        display_bar: function() {
            var self = this;
            var chart = this._super.apply(this, arguments);
            var text_list = $('g.nvd3.nv-wrap.nv-axis g.tick text')
            for ( var i = 0; i < text_list.length; i++ ) {
			    text_list[i].text = '111'
		    }
            return chart
        },
        // willStart: function () {
        //     var self = this;
        //     var res_super = this._super.apply(this, arguments);
        //     var text_list = $('g.nvd3.nv-wrap.nv-axis g.tick text')
        //     for ( var i = 0; i < text_list.length; i++ ) {
			//     text_list[i].text = '111'
		 //    }
		 //    return res_super
        // }
    })

});

nv.models.multiBar = function() {
    "use strict";

    //============================================================
    // Public Variables with Default Settings
    //------------------------------------------------------------

    var margin = {top: 0, right: 0, bottom: 0, left: 0}
        , width = 960
        , height = 500
        , x = d3.scale.ordinal()
        , y = d3.scale.linear()
        , id = Math.floor(Math.random() * 10000) //Create semi-unique ID in case user doesn't select one
        , container = null
        , getX = function(d) { return d.x }
        , getY = function(d) { return d.y }
        , forceY = [0] // 0 is forced by default.. this makes sense for the majority of bar graphs... user can always do chart.forceY([]) to remove
        , clipEdge = true
        , stacked = false
        , stackOffset = 'zero' // options include 'silhouette', 'wiggle', 'expand', 'zero', or a custom function
        , color = nv.utils.defaultColor()
        , hideable = false
        , barColor = null // adding the ability to set the color for each rather than the whole group
        , disabled // used in conjunction with barColor to communicate from multiBarHorizontalChart what series are disabled
        , duration = 500
        , xDomain
        , yDomain
        , xRange
        , yRange
        , groupSpacing = 0.1
        , dispatch = d3.dispatch('chartClick', 'elementClick', 'elementDblClick', 'elementMouseover', 'elementMouseout', 'elementMousemove', 'renderEnd')
        ;

    //============================================================
    // Private Variables
    //------------------------------------------------------------

    var x0, y0 //used to store previous scales
        , renderWatch = nv.utils.renderWatch(dispatch, duration)
        ;

    var last_datalength = 0;

    function chart(selection) {
        renderWatch.reset();
        selection.each(function(data) {
            var availableWidth = width - margin.left - margin.right,
                availableHeight = height - margin.top - margin.bottom + 10;

            container = d3.select(this);
            nv.utils.initSVG(container);
            var nonStackableCount = 0;
            // This function defines the requirements for render complete
            var endFn = function(d, i) {
                if (d.series === data.length - 1 && i === data[0].values.length - 1)
                    return true;
                return false;
            };

            if(hideable && data.length) hideable = [{
                values: data[0].values.map(function(d) {
                        return {
                            x: d.x,
                            y: 0,
                            series: d.series,
                            size: 0.01
                        };}
                )}];

            if (stacked) {
                var parsed = d3.layout.stack()
                    .offset(stackOffset)
                    .values(function(d){ return d.values })
                    .y(getY)
                (!data.length && hideable ? hideable : data);

                parsed.forEach(function(series, i){
                    // if series is non-stackable, use un-parsed data
                    if (series.nonStackable) {
                        data[i].nonStackableSeries = nonStackableCount++;
                        parsed[i] = data[i];
                    } else {
                        // don't stack this seires on top of the nonStackable seriees
                        if (i > 0 && parsed[i - 1].nonStackable){
                            parsed[i].values.map(function(d,j){
                                d.y0 -= parsed[i - 1].values[j].y;
                                d.y1 = d.y0 + d.y;
                            });
                        }
                    }
                });
                data = parsed;
            }
            //add series index and key to each data point for reference
            data.forEach(function(series, i) {
                series.values.forEach(function(point) {
                    point.series = i;
                    point.key = series.key;
                });
            });

            // HACK for negative value stacking
            if (stacked) {
                data[0].values.map(function(d,i) {
                    var posBase = 0, negBase = 0;
                    data.map(function(d, idx) {
                        if (!data[idx].nonStackable) {
                            var f = d.values[i]
                            f.size = Math.abs(f.y);
                            if (f.y<0)  {
                                f.y1 = negBase;
                                negBase = negBase - f.size;
                            } else
                            {
                                f.y1 = f.size + posBase;
                                posBase = posBase + f.size;
                            }
                        }

                    });
                });
            }
            // Setup Scales
            // remap and flatten the data for use in calculating the scales' domains
            var seriesData = (xDomain && yDomain) ? [] : // if we know xDomain and yDomain, no need to calculate
                data.map(function(d, idx) {
                    return d.values.map(function(d,i) {
                        return { x: getX(d,i), y: getY(d,i), y0: d.y0, y1: d.y1, idx:idx }
                    })
                });

            x.domain(xDomain || d3.merge(seriesData).map(function(d) { return d.x }))
                .rangeBands(xRange || [0, availableWidth], groupSpacing);

            y.domain(yDomain || d3.extent(d3.merge(seriesData).map(function(d) {
                var domain = d.y;
                // increase the domain range if this series is stackable
                if (stacked && !data[d.idx].nonStackable) {
                    if (d.y > 0){
                        domain = d.y1
                    } else {
                        domain = d.y1 + d.y
                    }
                }
                return domain;
            }).concat(forceY)))
            .range(yRange || [availableHeight, 0]);

            // If scale's domain don't have a range, slightly adjust to make one... so a chart can show a single data point
            if (x.domain()[0] === x.domain()[1])
                x.domain()[0] ?
                    x.domain([x.domain()[0] - x.domain()[0] * 0.01, x.domain()[1] + x.domain()[1] * 0.01])
                    : x.domain([-1,1]);

            if (y.domain()[0] === y.domain()[1])
                y.domain()[0] ?
                    y.domain([y.domain()[0] + y.domain()[0] * 0.01, y.domain()[1] - y.domain()[1] * 0.01])
                    : y.domain([-1,1]);

            x0 = x0 || x;
            y0 = y0 || y;

            // Setup containers and skeleton of chart
            var wrap = container.selectAll('g.nv-wrap.nv-multibar').data([data]);
            var wrapEnter = wrap.enter().append('g').attr('class', 'nvd3 nv-wrap nv-multibar');
            var defsEnter = wrapEnter.append('defs');
            var gEnter = wrapEnter.append('g');
            var g = wrap.select('g');

            gEnter.append('g').attr('class', 'nv-groups');
            wrap.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

            defsEnter.append('clipPath')
                .attr('id', 'nv-edge-clip-' + id)
                .append('rect');
            wrap.select('#nv-edge-clip-' + id + ' rect')
                .attr('width', availableWidth)
                .attr('height', availableHeight);

            // g.attr('clip-path', clipEdge ? 'url(#nv-edge-clip-' + id + ')' : '');

            var groups = wrap.select('.nv-groups').selectAll('.nv-group')
                .data(function(d) { return d }, function(d,i) { return i });
            groups.enter().append('g')
                .style('stroke-opacity', 1e-6)
                .style('fill-opacity', 1e-6);

            var exitTransition = renderWatch
                .transition(groups.exit().selectAll('rect.nv-bar'), 'multibarExit', Math.min(100, duration))
                .attr('y', function(d, i, j) {
                    var yVal = y0(0) || 0;
                    if (stacked) {
                        if (data[d.series] && !data[d.series].nonStackable) {
                            yVal = y0(d.y0);
                        }
                    }
                    return yVal;
                })
                .attr('height', 0)
                .remove();
            if (exitTransition.delay)
                exitTransition.delay(function(d,i) {
                    var delay = i * (duration / (last_datalength + 1)) - i;
                    return delay;
                });
            groups
                .attr('class', function(d,i) { return '11 nv-group nv-series-' + i })
                .classed('hover', function(d) {
                    return d.hover
                })
                .style('fill', function(d,i){ return color(d, i) })
                // .style('stroke', function(d,i){ return color(d, i) });
            groups
                .style('stroke-opacity', 1)
                .style('fill-opacity', 0.75);

            var bars = groups.selectAll('rect.nv-bar')
                .data(function(d) { return (hideable && !data.length) ? hideable.values : d.values });
            bars.exit().remove();

            var barsEnter = bars.enter().append('rect')
                    .attr('class', function(d,i) { return getY(d,i) < 0 ? 'nv-bar negative' : '1nv-bar positive'})
                    .attr('x', function(d,i,j) {
                        return stacked && !data[j].nonStackable ? 0 : (j * x.rangeBand() / data.length )
                    })
                    .attr('y', function(d,i,j) { return y0(stacked && !data[j].nonStackable ? d.y0 : 0) || 0 })
                    .attr('height', 0)
                    .attr('width', function(d,i,j) { return x.rangeBand() / (stacked && !data[j].nonStackable ? 1 : data.length) })
                    .attr('transform', function(d,i) { return 'translate(' + x(getX(d,i)) + ',0)'; })
                ;
            bars
                .style('fill', function(d,i,j){ return color(d, j, i);  })
                .style('stroke', function(d,i,j){ return color(d, j, i); })
                .on('mouseover', function(d,i) { //TODO: figure out why j works above, but not here
                    d3.select(this).classed('hover', true);
                    dispatch.elementMouseover({
                        data: d,
                        index: i,
                        color: d3.select(this).style("fill")
                    });
                })
                .on('mouseout', function(d,i) {
                    d3.select(this).classed('hover', false);
                    dispatch.elementMouseout({
                        data: d,
                        index: i,
                        color: d3.select(this).style("fill")
                    });
                })
                .on('mousemove', function(d,i) {
                    dispatch.elementMousemove({
                        data: d,
                        index: i,
                        color: d3.select(this).style("fill")
                    });
                })
                .on('click', function(d,i) {
                    var element = this;
                    dispatch.elementClick({
                        data: d,
                        index: i,
                        color: d3.select(this).style("fill"),
                        event: d3.event,
                        element: element
                    });
                    d3.event.stopPropagation();
                })
                .on('dblclick', function(d,i) {
                    dispatch.elementDblClick({
                        data: d,
                        index: i,
                        color: d3.select(this).style("fill")
                    });
                    d3.event.stopPropagation();
                });
            bars
                .attr('class', function(d,i) { return getY(d,i) < 0 ? 'nv-bar negative' : 'nv-bar positive'})
                .attr('transform', function(d,i) { return 'translate(' + x(getX(d,i)) + ',0)'; })

            if (barColor) {
                if (!disabled) disabled = data.map(function() { return true });
                bars
                    .style('fill', function(d,i,j) { return d3.rgb(barColor(d,i)).darker(  disabled.map(function(d,i) { return i }).filter(function(d,i){ return !disabled[i]  })[j]   ).toString(); })
                    .style('stroke', function(d,i,j) { return d3.rgb(barColor(d,i)).darker(  disabled.map(function(d,i) { return i }).filter(function(d,i){ return !disabled[i]  })[j]   ).toString(); });
            }

            var barSelection =
                bars.watchTransition(renderWatch, 'multibar', Math.min(250, duration))
                    .delay(function(d,i) {
                        return i * duration / data[0].values.length;
                    });
            if (stacked){
                barSelection
                    .attr('y', function(d,i,j) {
                        var yVal = 0;
                        // if stackable, stack it on top of the previous series
                        if (!data[j].nonStackable) {
                            yVal = y(d.y1);
                        } else {
                            if (getY(d,i) < 0){
                                yVal = y(0);
                            } else {
                                if (y(0) - y(getY(d,i)) < -1){
                                    yVal = y(0) - 1;
                                } else {
                                    yVal = y(getY(d, i)) || 0;
                                }
                            }
                        }
                        return yVal;
                    })
                    .attr('height', function(d,i,j) {
                        if (!data[j].nonStackable) {
                            return Math.max(Math.abs(y(d.y+d.y0) - y(d.y0)), 0);
                        } else {
                            return Math.max(Math.abs(y(getY(d,i)) - y(0)), 0) || 0;
                        }
                    })
                    .attr('x', function(d,i,j) {
                        var width = 0;
                        if (data[j].nonStackable) {
                            width = d.series * x.rangeBand() / data.length;
                            if (data.length !== nonStackableCount){
                                width = data[j].nonStackableSeries * x.rangeBand()/(nonStackableCount*2);
                            }
                        }
                        return width;
                    })
                    .attr('width', function(d,i,j){
                        if (!data[j].nonStackable) {
                            return x.rangeBand();
                        } else {
                            // if all series are nonStacable, take the full width
                            var width = (x.rangeBand() / nonStackableCount);
                            // otherwise, nonStackable graph will be only taking the half-width
                            // of the x rangeBand
                            if (data.length !== nonStackableCount) {
                                width = x.rangeBand()/(nonStackableCount*2);
                            }
                            return width;
                        }
                    });
            }
            else {
                barSelection
                    .attr('x', function(d,i) {
                        return d.series * x.rangeBand() / data.length;
                    })
                    .attr('width', x.rangeBand() / data.length)
                    .attr('y', function(d,i) {
                        return getY(d,i) < 0 ?
                            y(0) :
                                y(0) - y(getY(d,i)) < 1 ?
                            y(0) - 1 :
                            y(getY(d,i)) || 0;
                    })
                    .attr('height', function(d,i) {
                        return Math.max(Math.abs(y(getY(d,i)) - y(0)),1) || 0;
                    });
            }

            //store old scales for use in transitions on update
            x0 = x.copy();
            y0 = y.copy();

            // keep track of the last data value length for transition calculations
            if (data[0] && data[0].values) {
                last_datalength = data[0].values.length;
            }

        });

        renderWatch.renderEnd('multibar immediate');

        return chart;
    }

    //============================================================
    // Expose Public Variables
    //------------------------------------------------------------

    chart.dispatch = dispatch;

    chart.options = nv.utils.optionsFunc.bind(chart);

    chart._options = Object.create({}, {
        // simple options, just get/set the necessary values
        width:   {get: function(){return width;}, set: function(_){width=_;}},
        height:  {get: function(){return height;}, set: function(_){height=_;}},
        x:       {get: function(){return getX;}, set: function(_){getX=_;}},
        y:       {get: function(){return getY;}, set: function(_){getY=_;}},
        xScale:  {get: function(){return x;}, set: function(_){x=_;}},
        yScale:  {get: function(){return y;}, set: function(_){y=_;}},
        xDomain: {get: function(){return xDomain;}, set: function(_){xDomain=_;}},
        yDomain: {get: function(){return yDomain;}, set: function(_){yDomain=_;}},
        xRange:  {get: function(){return xRange;}, set: function(_){xRange=_;}},
        yRange:  {get: function(){return yRange;}, set: function(_){yRange=_;}},
        forceY:  {get: function(){return forceY;}, set: function(_){forceY=_;}},
        stacked: {get: function(){return stacked;}, set: function(_){stacked=_;}},
        stackOffset: {get: function(){return stackOffset;}, set: function(_){stackOffset=_;}},
        clipEdge:    {get: function(){return clipEdge;}, set: function(_){clipEdge=_;}},
        disabled:    {get: function(){return disabled;}, set: function(_){disabled=_;}},
        id:          {get: function(){return id;}, set: function(_){id=_;}},
        hideable:    {get: function(){return hideable;}, set: function(_){hideable=_;}},
        groupSpacing:{get: function(){return groupSpacing;}, set: function(_){groupSpacing=_;}},

        // options that require extra logic in the setter
        margin: {get: function(){return margin;}, set: function(_){
            margin.top    = _.top    !== undefined ? _.top    : margin.top;
            margin.right  = _.right  !== undefined ? _.right  : margin.right;
            margin.bottom = _.bottom !== undefined ? _.bottom : margin.bottom;
            margin.left   = _.left   !== undefined ? _.left   : margin.left;
        }},
        duration: {get: function(){return duration;}, set: function(_){
            duration = _;
            renderWatch.reset(duration);
        }},
        color:  {get: function(){return color;}, set: function(_){
            color = nv.utils.getColor(_);
        }},
        barColor:  {get: function(){return barColor;}, set: function(_){
            barColor = _ ? nv.utils.getColor(_) : null;
        }}
    });

    nv.utils.initOptions(chart);

    return chart;
};