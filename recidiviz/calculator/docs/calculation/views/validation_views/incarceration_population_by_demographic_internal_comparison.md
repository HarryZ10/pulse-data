## validation_views.incarceration_population_by_demographic_internal_comparison
 Comparison of various internal incarceration population counts by facility 

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=validation_views&t=incarceration_population_by_demographic_internal_comparison)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=validation_views&t=incarceration_population_by_demographic_internal_comparison)
<br/>

#### Dependency Trees

##### Parentage
[validation_views.incarceration_population_by_demographic_internal_comparison](../validation_views/incarceration_population_by_demographic_internal_comparison.md) <br/>
|--[public_dashboard_views.incarceration_population_by_facility_by_demographics](../public_dashboard_views/incarceration_population_by_facility_by_demographics.md) <br/>
|----static_reference_tables.state_incarceration_facility_capacity ([BQ Staging](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=static_reference_tables&t=state_incarceration_facility_capacity)) ([BQ Prod](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=static_reference_tables&t=state_incarceration_facility_capacity)) <br/>
|----[shared_metric_views.single_day_incarceration_population_for_spotlight](../shared_metric_views/single_day_incarceration_population_for_spotlight.md) <br/>
|------[dataflow_metrics_materialized.most_recent_single_day_incarceration_population_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_single_day_incarceration_population_metrics_included_in_state_population.md) <br/>
|--------[dataflow_metrics_materialized.most_recent_incarceration_population_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_population_metrics_included_in_state_population.md) <br/>
|----------[dataflow_metrics.incarceration_population_metrics](../../metrics/incarceration/incarceration_population_metrics.md) <br/>
|--[public_dashboard_views.incarceration_population_by_admission_reason](../public_dashboard_views/incarceration_population_by_admission_reason.md) <br/>
|----[shared_metric_views.single_day_incarceration_population_for_spotlight](../shared_metric_views/single_day_incarceration_population_for_spotlight.md) <br/>
|------[dataflow_metrics_materialized.most_recent_single_day_incarceration_population_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_single_day_incarceration_population_metrics_included_in_state_population.md) <br/>
|--------[dataflow_metrics_materialized.most_recent_incarceration_population_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_population_metrics_included_in_state_population.md) <br/>
|----------[dataflow_metrics.incarceration_population_metrics](../../metrics/incarceration/incarceration_population_metrics.md) <br/>


##### Descendants
This view has no child dependencies.