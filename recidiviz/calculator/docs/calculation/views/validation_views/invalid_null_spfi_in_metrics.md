## validation_views.invalid_null_spfi_in_metrics
Metrics with invalid null values for specialized_purpose_for_incarceration.

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=validation_views&t=invalid_null_spfi_in_metrics)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=validation_views&t=invalid_null_spfi_in_metrics)
<br/>

#### Dependency Trees

##### Parentage
[validation_views.invalid_null_spfi_in_metrics](../validation_views/invalid_null_spfi_in_metrics.md) <br/>
|--[dataflow_metrics_materialized.most_recent_incarceration_population_metrics_not_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_population_metrics_not_included_in_state_population.md) <br/>
|----[dataflow_metrics.incarceration_population_metrics](../../metrics/incarceration/incarceration_population_metrics.md) <br/>
|--[dataflow_metrics_materialized.most_recent_incarceration_population_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_population_metrics_included_in_state_population.md) <br/>
|----[dataflow_metrics.incarceration_population_metrics](../../metrics/incarceration/incarceration_population_metrics.md) <br/>
|--[dataflow_metrics_materialized.most_recent_incarceration_commitment_from_supervision_metrics_not_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_commitment_from_supervision_metrics_not_included_in_state_population.md) <br/>
|----[dataflow_metrics.incarceration_commitment_from_supervision_metrics](../../metrics/incarceration/incarceration_commitment_from_supervision_metrics.md) <br/>
|--[dataflow_metrics_materialized.most_recent_incarceration_commitment_from_supervision_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_commitment_from_supervision_metrics_included_in_state_population.md) <br/>
|----[dataflow_metrics.incarceration_commitment_from_supervision_metrics](../../metrics/incarceration/incarceration_commitment_from_supervision_metrics.md) <br/>
|--[dataflow_metrics_materialized.most_recent_incarceration_admission_metrics_not_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_admission_metrics_not_included_in_state_population.md) <br/>
|----[dataflow_metrics.incarceration_admission_metrics](../../metrics/incarceration/incarceration_admission_metrics.md) <br/>
|--[dataflow_metrics_materialized.most_recent_incarceration_admission_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_admission_metrics_included_in_state_population.md) <br/>
|----[dataflow_metrics.incarceration_admission_metrics](../../metrics/incarceration/incarceration_admission_metrics.md) <br/>


##### Descendants
This view has no child dependencies.