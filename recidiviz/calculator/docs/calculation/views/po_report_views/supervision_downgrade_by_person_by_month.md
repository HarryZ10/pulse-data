## po_report_views.supervision_downgrade_by_person_by_month
Supervision downgrades by person by month

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=po_report_views&t=supervision_downgrade_by_person_by_month)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=po_report_views&t=supervision_downgrade_by_person_by_month)
<br/>

#### Dependency Trees

##### Parentage
[po_report_views.supervision_downgrade_by_person_by_month](../po_report_views/supervision_downgrade_by_person_by_month.md) <br/>
|--[dataflow_metrics_materialized.most_recent_supervision_downgrade_metrics](../dataflow_metrics_materialized/most_recent_supervision_downgrade_metrics.md) <br/>
|----[dataflow_metrics.supervision_downgrade_metrics](../../metrics/supervision/supervision_downgrade_metrics.md) <br/>


##### Descendants
[po_report_views.supervision_downgrade_by_person_by_month](../po_report_views/supervision_downgrade_by_person_by_month.md) <br/>
|--[po_report_views.report_data_by_person_by_month](../po_report_views/report_data_by_person_by_month.md) <br/>
|----[linestaff_data_validation.violations](../linestaff_data_validation/violations.md) <br/>
|------[linestaff_data_validation.looker_dashboard](../linestaff_data_validation/looker_dashboard.md) <br/>
|----[po_report_views.report_data_by_officer_by_month](../po_report_views/report_data_by_officer_by_month.md) <br/>
|------[linestaff_data_validation.metrics_from_po_report](../linestaff_data_validation/metrics_from_po_report.md) <br/>
|------[linestaff_data_validation.po_events](../linestaff_data_validation/po_events.md) <br/>
|------[po_report_views.po_monthly_report_data](../po_report_views/po_monthly_report_data.md) <br/>
|--------[validation_views.po_report_avgs_per_district_state](../validation_views/po_report_avgs_per_district_state.md) <br/>
|--------[validation_views.po_report_clients](../validation_views/po_report_clients.md) <br/>
|--------[validation_views.po_report_distinct_by_officer_month](../validation_views/po_report_distinct_by_officer_month.md) <br/>
|--------[validation_views.po_report_missing_fields](../validation_views/po_report_missing_fields.md) <br/>
|--------[validation_views.po_report_missing_fields_errors](../validation_views/po_report_missing_fields_errors.md) <br/>
|----[validation_views.case_termination_by_type_comparison](../validation_views/case_termination_by_type_comparison.md) <br/>
|----[validation_views.case_termination_by_type_comparisonabsconsions_errors](../validation_views/case_termination_by_type_comparisonabsconsions_errors.md) <br/>
|----[validation_views.case_termination_by_type_comparisondischarges_errors](../validation_views/case_termination_by_type_comparisondischarges_errors.md) <br/>
