## validation_views.ftr_referrals_comparison
FTR program referral count comparison per metric period

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=validation_views&t=ftr_referrals_comparison)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=validation_views&t=ftr_referrals_comparison)
<br/>

#### Dependency Trees

##### Parentage
[validation_views.ftr_referrals_comparison](../validation_views/ftr_referrals_comparison.md) <br/>
|--[dashboard_views.ftr_referrals_by_race_and_ethnicity_by_period](../dashboard_views/ftr_referrals_by_race_and_ethnicity_by_period.md) <br/>
|----[shared_metric_views.event_based_supervision_populations](../shared_metric_views/event_based_supervision_populations.md) <br/>
|------[dataflow_metrics_materialized.most_recent_supervision_population_metrics](../dataflow_metrics_materialized/most_recent_supervision_population_metrics.md) <br/>
|--------[dataflow_metrics.supervision_population_metrics](../../metrics/supervision/supervision_population_metrics.md) <br/>
|----[shared_metric_views.event_based_program_referrals](../shared_metric_views/event_based_program_referrals.md) <br/>
|------[dataflow_metrics_materialized.most_recent_program_referral_metrics](../dataflow_metrics_materialized/most_recent_program_referral_metrics.md) <br/>
|--------[dataflow_metrics.program_referral_metrics](../../metrics/program/program_referral_metrics.md) <br/>
|--[dashboard_views.ftr_referrals_by_lsir_by_period](../dashboard_views/ftr_referrals_by_lsir_by_period.md) <br/>
|----[shared_metric_views.event_based_supervision_populations](../shared_metric_views/event_based_supervision_populations.md) <br/>
|------[dataflow_metrics_materialized.most_recent_supervision_population_metrics](../dataflow_metrics_materialized/most_recent_supervision_population_metrics.md) <br/>
|--------[dataflow_metrics.supervision_population_metrics](../../metrics/supervision/supervision_population_metrics.md) <br/>
|----[shared_metric_views.event_based_program_referrals](../shared_metric_views/event_based_program_referrals.md) <br/>
|------[dataflow_metrics_materialized.most_recent_program_referral_metrics](../dataflow_metrics_materialized/most_recent_program_referral_metrics.md) <br/>
|--------[dataflow_metrics.program_referral_metrics](../../metrics/program/program_referral_metrics.md) <br/>
|--[dashboard_views.ftr_referrals_by_gender_by_period](../dashboard_views/ftr_referrals_by_gender_by_period.md) <br/>
|----[shared_metric_views.event_based_supervision_populations](../shared_metric_views/event_based_supervision_populations.md) <br/>
|------[dataflow_metrics_materialized.most_recent_supervision_population_metrics](../dataflow_metrics_materialized/most_recent_supervision_population_metrics.md) <br/>
|--------[dataflow_metrics.supervision_population_metrics](../../metrics/supervision/supervision_population_metrics.md) <br/>
|----[shared_metric_views.event_based_program_referrals](../shared_metric_views/event_based_program_referrals.md) <br/>
|------[dataflow_metrics_materialized.most_recent_program_referral_metrics](../dataflow_metrics_materialized/most_recent_program_referral_metrics.md) <br/>
|--------[dataflow_metrics.program_referral_metrics](../../metrics/program/program_referral_metrics.md) <br/>
|--[dashboard_views.ftr_referrals_by_age_by_period](../dashboard_views/ftr_referrals_by_age_by_period.md) <br/>
|----[shared_metric_views.event_based_supervision_populations](../shared_metric_views/event_based_supervision_populations.md) <br/>
|------[dataflow_metrics_materialized.most_recent_supervision_population_metrics](../dataflow_metrics_materialized/most_recent_supervision_population_metrics.md) <br/>
|--------[dataflow_metrics.supervision_population_metrics](../../metrics/supervision/supervision_population_metrics.md) <br/>
|----[shared_metric_views.event_based_program_referrals](../shared_metric_views/event_based_program_referrals.md) <br/>
|------[dataflow_metrics_materialized.most_recent_program_referral_metrics](../dataflow_metrics_materialized/most_recent_program_referral_metrics.md) <br/>
|--------[dataflow_metrics.program_referral_metrics](../../metrics/program/program_referral_metrics.md) <br/>


##### Descendants
This view has no child dependencies.