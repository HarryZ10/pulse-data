## dashboard_views.admissions_by_type_by_period
Admissions by type by metric period months.

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=dashboard_views&t=admissions_by_type_by_period)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=dashboard_views&t=admissions_by_type_by_period)
<br/>

#### Dependency Trees

##### Parentage
[dashboard_views.admissions_by_type_by_period](../dashboard_views/admissions_by_type_by_period.md) <br/>
|--[shared_metric_views.event_based_commitments_from_supervision](../shared_metric_views/event_based_commitments_from_supervision.md) <br/>
|----[dataflow_metrics_materialized.most_recent_incarceration_commitment_from_supervision_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_commitment_from_supervision_metrics_included_in_state_population.md) <br/>
|------[dataflow_metrics.incarceration_commitment_from_supervision_metrics](../../metrics/incarceration/incarceration_commitment_from_supervision_metrics.md) <br/>
|--[shared_metric_views.event_based_admissions](../shared_metric_views/event_based_admissions.md) <br/>
|----[dataflow_metrics_materialized.most_recent_incarceration_admission_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_admission_metrics_included_in_state_population.md) <br/>
|------[dataflow_metrics.incarceration_admission_metrics](../../metrics/incarceration/incarceration_admission_metrics.md) <br/>


##### Descendants
This view has no child dependencies.