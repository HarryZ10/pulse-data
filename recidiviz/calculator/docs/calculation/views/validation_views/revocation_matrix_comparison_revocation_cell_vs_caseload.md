## validation_views.revocation_matrix_comparison_revocation_cell_vs_caseload

Revocation matrix comparison of summed revocation counts between the grid cells and the month chart 

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=validation_views&t=revocation_matrix_comparison_revocation_cell_vs_caseload)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=validation_views&t=revocation_matrix_comparison_revocation_cell_vs_caseload)
<br/>

#### Dependency Trees

##### Parentage
[validation_views.revocation_matrix_comparison_revocation_cell_vs_caseload](../validation_views/revocation_matrix_comparison_revocation_cell_vs_caseload.md) <br/>
|--[dashboard_views.revocations_matrix_filtered_caseload](../dashboard_views/revocations_matrix_filtered_caseload.md) <br/>
|----[shared_metric_views.revocations_matrix_by_person](../shared_metric_views/revocations_matrix_by_person.md) <br/>
|------[shared_metric_views.event_based_commitments_from_supervision_for_matrix](../shared_metric_views/event_based_commitments_from_supervision_for_matrix.md) <br/>
|--------[reference_views.agent_external_id_to_full_name](../reference_views/agent_external_id_to_full_name.md) <br/>
|----------[reference_views.augmented_agent_info](../reference_views/augmented_agent_info.md) <br/>
|------------state.state_agent ([BQ Staging](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=state&t=state_agent)) ([BQ Prod](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=state&t=state_agent)) <br/>
|--------[dataflow_metrics_materialized.most_recent_incarceration_commitment_from_supervision_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_commitment_from_supervision_metrics_included_in_state_population.md) <br/>
|----------[dataflow_metrics.incarceration_commitment_from_supervision_metrics](../../metrics/incarceration/incarceration_commitment_from_supervision_metrics.md) <br/>
|--[dashboard_views.revocations_matrix_cells](../dashboard_views/revocations_matrix_cells.md) <br/>
|----[shared_metric_views.revocations_matrix_by_person](../shared_metric_views/revocations_matrix_by_person.md) <br/>
|------[shared_metric_views.event_based_commitments_from_supervision_for_matrix](../shared_metric_views/event_based_commitments_from_supervision_for_matrix.md) <br/>
|--------[reference_views.agent_external_id_to_full_name](../reference_views/agent_external_id_to_full_name.md) <br/>
|----------[reference_views.augmented_agent_info](../reference_views/augmented_agent_info.md) <br/>
|------------state.state_agent ([BQ Staging](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=state&t=state_agent)) ([BQ Prod](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=state&t=state_agent)) <br/>
|--------[dataflow_metrics_materialized.most_recent_incarceration_commitment_from_supervision_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_commitment_from_supervision_metrics_included_in_state_population.md) <br/>
|----------[dataflow_metrics.incarceration_commitment_from_supervision_metrics](../../metrics/incarceration/incarceration_commitment_from_supervision_metrics.md) <br/>


##### Descendants
This view has no child dependencies.