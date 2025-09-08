odoo.define('ars_crm_dashboard.Dashboard', function (require) {
    "use strict";
    
    var core = require('web.core');
    var _t = core._t;
    var framework = require('web.framework');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var QWeb = core.qweb;
    
    
    var CRMMainDashboard = Widget.extend({
        template: 'CRM_Main_Dashboard',
        events: {
            'click #filter_leads_generated': 'render_filter_leads_generated',
            'click .count' : 'render_action',
            'click #refresh_leads_generated': 'render_lead_generated_graphs',
            'click #refresh_opportunities': 'render_opportunities_graphs',
            'click #refresh_quotations': 'render_quotations_graphs', 
            'click #filter_leads_generated_button': _.debounce(function(){
                var self = this;
                self.yearLeadSelect = $('#lead-year-select').val();
                self.salesPersonLeadSelect = $('#lead-sales-person-select').val();
                self.leadModelSelect = $('#lead-model-select').val();
                setTimeout(function(){self.render_lead_generated_graphs("filter");},200);
            },200,true),
            'click #filter_opportunities_button': _.debounce(function(){
                var self = this;
                self.yearOpportunitiesSelect = $('#opportunities-year-select').val();
                self.salesPersonOpportunitiesSelect = $('#opportunities-sales-person-select').val();
                self.ModelOpportunitiesSelect = $('#opportunities-model-select').val();
                setTimeout(function(){self.render_opportunities_graphs("filter");},200);
            },200,true),
            'click #filter_quotations_button': _.debounce(function(){
                var self = this;
                self.yearQuotationSelect = $('#quotations-year-select').val();
                self.salesPersonQuotationSelect = $('#quotations-sales-person-select').val();
                self.ModelQuotationSelect = $('#quotations-model-select').val();
                setTimeout(function(){self.render_quotations_graphs("filter");},200);
            },200,true),
            'click #filter_model_wise_sale_button': _.debounce(function(){
                var self = this;
                self.yearModelWiseSaleSelect = $('#model-wise-year-select').val();
                self.salesPersonModelWiseSaleSelect = $('#model-wise-sales-person-select').val();
                setTimeout(function(){self.render_model_wise_sale_graphs("filter");},200);
            },200,true),
        },
        init: function(parent, action) {
            this.actionManager = parent;
            this.action = action;
            this.domain = [];
            this.dashboards_templates = ['MainDashboard'];
            return this._super.apply(this, arguments);
        },
    
        willStart: function() {
            var self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();
            });
        },
    
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                setTimeout(function(){
                    self.render_dashboards();
                },0);
            });
        },
    
        fetch_data: function() {
            var self = this;
            var dealer_rpc =  this._rpc({
                    model: 'crm.lead',
                    method: 'get_dealer_list'
            }).then(function(result) {
                self.dealer_data = result[0];
            });
            var revenue_rpc =  this._rpc({
                model: 'crm.lead',
                method: 'get_renvenue'
            }).then(function(result) {
                self.revenue_data = result;
            });
            var year_list_rpc = this._rpc({
                model: 'crm.lead',
                method: 'get_year_user_models_list_data'
            }).then(function(result) {
                self.year_data = result[0];
                self.sales_person_data = result[1];
                self.model_data = result[2];
            });
            return $.when(dealer_rpc,revenue_rpc,year_list_rpc);
        },
    
        render_dashboards: function() {
            var self = this;
            // self.$el.append(QWeb.render('CRM_Main_Dashboard', {widget: self}));
            self.render_graphs();
            self.$el.find('.leads-generated-filter-wrapper,.opportunities-filter-wrapper,.quotations-filter-wrapper,.model-wise-sale-filter-wrapper').css("display", "none");
            self.$el.find('#filter_leads_generated').click(function(){
                self.$el.find('.leads-generated-filter-wrapper').css("display", "");
            });
            self.$el.find('#filter_opportunities').click(function(){
                self.$el.find('.opportunities-filter-wrapper').css("display", "");
            });
            self.$el.find('#filter_quotations').click(function(){
                self.$el.find('.quotations-filter-wrapper').css("display", "");
            });
            self.$el.find('#filter_model_wise_sale').click(function(){
                self.$el.find('.model-wise-sale-filter-wrapper').css("display", "");
            });
            self.$el.find('#close_leads_generated_filter,#filter_leads_generated_button').click(function(){
                self.$el.find('.leads-generated-filter-wrapper').css("display", "none");
            });
            self.$el.find('#close_opportunities_filter,#filter_opportunities_button').click(function(){
                self.$el.find('.opportunities-filter-wrapper').css("display", "none");
            });
            self.$el.find('#close_quotations_filter,#filter_quotations_button').click(function(){
                self.$el.find('.quotations-filter-wrapper').css("display", "none");
            });
            self.$el.find('#close_model_wise_sale_filter,#filter_model_wise_sale_button').click(function(){
                self.$el.find('.model-wise-sale-filter-wrapper').css("display", "none");
            });
            return true;
        },
        render_filter_leads_generated: function(){
            var self = this;
        },
        render_graphs: function(){
            var self = this;
            self.render_lead_generated_graphs();
            self.render_opportunities_graphs();
            self.render_quotations_graphs();
            self.render_model_wise_sale_graphs();
        },
        render_lead_generated_graphs: function(filter){
            var self = this;
            var params = {}
            if (filter == 'filter') {params = {'lead_year': self.yearLeadSelect, 'sales_person': self.salesPersonLeadSelect, 'model':self.leadModelSelect}}
            var lead_generated =  this._rpc({
                model: 'crm.lead',
                method: 'get_lead_portlet_data',
                kwargs: params
            }).then(function(result) {
                var filter_string = ''
                if(filter == 'filter'){filter_string = '<b style="color:#a94442; font-size: small;">' + result[3] + '</b> <br/> Leads Generated in <b>' + result[0] +'</b>'}
                else {filter_string = 'Leads Generated in <b>' + result[0] + '</b>'}
                Highcharts.chart('leades-generated', {
                    chart: {
                        type: 'column'
                    },
                    title: {
                        text: filter_string
                    },
                    xAxis: {
                        categories: result[1],
                        title: {
                            text: 'Month(s)'
                        },
                        crosshair: true
                    },
                    yAxis: {
                        min: 0,
                        title: {
                            text: 'Lead Count'
                        }
                    },
                    tooltip: {
                        headerFormat: '<span style="font-size:10px; font-weight: bold;">{point.key}</span><table>',
                        pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
                            '<td style="padding:0"><b>{point.y:.0f}</b></td></tr>',
                        footerFormat: '</table>',
                        shared: true,
                        useHTML: true
                    },
                    plotOptions: {
                        column: {
                            // pointPadding: 0.2,
                            borderWidth: 0
                        },
                        series: {
                            borderWidth: 0,
                            dataLabels: {
                                enabled: true,
                                format: '{point.y:.0f}'
                            }
                        }
                    },
                    credits: {
                        enabled: false
                    },
                    series: [{
                        name: 'Count',
                        data: result[2],
                        showInLegend: false,  
                
                    }]
                });
            });
            return $.when(lead_generated);
        },
        render_opportunities_graphs: function(filter){
            var self = this;
            var params = {}
            if (filter == 'filter') {params = {'opportunity_year': self.yearOpportunitiesSelect, 'sales_person': self.salesPersonOpportunitiesSelect, 'model': self.ModelOpportunitiesSelect}}
            var opportunities_generated =  this._rpc({
                model: 'crm.lead',
                method: 'get_opportunities_portlet_data',
                kwargs: params
            }).then(function(result) {
                var filter_string = ''
                if(filter == 'filter'){filter_string = '<b style="color:#a94442; font-size: small;">' + result[3] + '</b> <br/> Historic Converted Opportunities by Stage <b>' + result[0] +'</b>'}
                else {filter_string = 'Historic Converted Opportunities by Stage <b>' + result[0] + '</b>'}
                Highcharts.chart('opportunities', {
                    chart: {
                        type: 'column'
                    },
                    title: {
                        align: 'left',
                        text: filter_string
                    },
                    accessibility: {
                        announceNewData: {
                            enabled: true
                        }
                    },
                    xAxis: {
                        type: 'category',
                        title: {
                            text: 'Stages'
                        }
                    },
                    yAxis: {
                        title: {
                            text: 'Count'
                        }
                
                    },
                    legend: {
                        enabled: false
                    },
                    plotOptions: {
                        series: {
                            borderWidth: 0,
                            dataLabels: {
                                enabled: true,
                                format: '{point.y:.0f}'
                            }
                        }
                    },
                    credits: {
                        enabled: false
                    },
                
                    tooltip: {
                        headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
                        pointFormat: '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.0f}</b><br/>'
                    },
                
                    series: [
                        {
                            name: 'Opportunities',
                            colorByPoint: true,
                            data: result[1]
                        }
                    ],
                    drilldown: {
                        breadcrumbs: {
                            position: {
                                align: 'right'
                            }
                        },
                        series: result[2]
                    }
                });
            });
            return $.when(opportunities_generated);
        },
        render_quotations_graphs: function(filter){
            var self = this;
            var params = {}
            if (filter == 'filter') {params = {'quotation_year': self.yearQuotationSelect, 'sales_person': self.salesPersonQuotationSelect, 'model':self.ModelQuotationSelect}}
            var quotation_generated =  this._rpc({
                model: 'crm.lead',
                method: 'get_quotations_portlet_data',
                kwargs: params
            }).then(function(result) {
                var filter_string = ''
                if(filter == 'filter'){filter_string = '<b style="color:#a94442; font-size: small;">' + result[3] + '</b> <br/> Monthly Quotations / Sale Order Range <b>' + result[0] +'</b>'}
                else {filter_string = 'Monthly Quotations / Sale Order Range <b>' + result[0] + '</b>'}
                Highcharts.chart('quotations', {
                    chart: {
                        type: 'spline'
                    },
                    title: {
                        text: filter_string //'Monthly Quotations Range in 2022'
                    },
                    xAxis: {
                        categories: result[1],
                        accessibility: {
                            description: 'Months of the year'
                        },
                        title: {
                            text: 'Month(s)'
                        },
                    },
                    yAxis: {
                        title: {
                            text: 'Quotations'
                        },
                        labels: {
                            formatter: function () {
                                return this.value;
                            }
                        }
                    },
                    plotOptions: {
                        spline: {
                            dataLabels: {
                                enabled: true
                            },
                            enableMouseTracking: true,
                            marker: {
                                radius: 4,
                                lineColor: '#666666',
                                lineWidth: 1
                            }
                        }
                    },
                    credits: {
                        enabled: false
                    },
                    series: [{
                        name: 'Sent',
                        marker: {
                            symbol: 'square'
                        },
                        data: result[2],
                    }, {
                        name: 'Cancelled',
                        marker: {
                            symbol: 'square'
                        },
                        data: result[4],
                    },
                    {
                        name: 'Sales Order',
                        marker: {
                            symbol: 'circle'
                        },
                        data: result[5],
                    }]
                });
            });
            return $.when(quotation_generated);
        },
        render_model_wise_sale_graphs: function(filter){
            var self = this;
            var params = {}
            if (filter == 'filter') {params = {'model_wise_sale_year': self.yearModelWiseSaleSelect, 'sales_person': self.salesPersonModelWiseSaleSelect}}
            var model_wise_sale = this._rpc({
                model: 'crm.lead',
                method: 'get_model_wise_sale_portlet_data',
                kwargs: params
            }).then(function(result) {
                var filter_string = ''
                if(filter == 'filter'){filter_string = '<b style="color:#a94442; font-size: small;">' + result[3] + '</b> <br/> Leads Generated in <b>' + result[0] +'</b>'}
                else {filter_string = 'Leads Generated in <b>' + result[0] + '</b>'}
                Highcharts.chart('model-wise-sale', {
                chart: {
                    type: 'pie'
                },
                title: {
                        text: filter_string,
                        align: 'left'
                    },
                    accessibility: {
                        announceNewData: {
                            enabled: true
                        },
                        point: {
                            valueSuffix: '%'
                        }
                    },

                    plotOptions: {
                        series: {
                            allowPointSelect: true,
                            cursor: 'pointer',
                            dataLabels: {
                                padding: 0,
                                allowOverlap: true,
                                enabled: true,
                                format: '{point.name}: {point.y:.0f}'
                            }
                        }
                    },

                    tooltip: {
                        headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
                        pointFormat: '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.0f}</b><br/>'
                    },
                    credits: {
                        enabled: false
                    },
                    series: [
                        {
                            name: 'Models',
                            colorByPoint: true,
                            data: result[1]
                        }
                    ],
                    drilldown: {
                        series: result[2]
                    }
                });

            });
            return $.when(model_wise_sale);
        },
        render_action: function(){
            var self = this;
            self.do_action({
                'name': _t("Pipeline"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
                domain: [['type','=','opportunity'],['team_id.team_type','=','sales'],'|',['company_id','=',parseInt(self.dealer_data)],['company_id.parent_id','=',parseInt(self.dealer_data)]], 
                // //,['company_id','=',self.company_id != undefined ? parseInt(self.company_id) : parseInt(self.current_company)]
                context: {
                    'tree_view_ref': 'crm.crm_case_tree_view_oppor',
                    'form_view_ref': 'crm.crm_case_form_view_oppor'
                },
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            });
        },
        reload: function () {
            window.location.href = this.href;
        },
        
        });
    
    core.action_registry.add('ac_main_dashboard', CRMMainDashboard);
    
    return CRMMainDashboard;

});