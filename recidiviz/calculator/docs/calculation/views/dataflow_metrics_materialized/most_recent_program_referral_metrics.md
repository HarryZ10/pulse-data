## dataflow_metrics_materialized.most_recent_program_referral_metrics
program_referral_metrics for the most recent job run

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=dataflow_metrics_materialized&t=most_recent_program_referral_metrics)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=dataflow_metrics_materialized&t=most_recent_program_referral_metrics)
<br/>

#### Dependency Trees

##### Parentage
[dataflow_metrics_materialized.most_recent_program_referral_metrics](../dataflow_metrics_materialized/most_recent_program_referral_metrics.md) <br/>
|--[dataflow_metrics.program_referral_metrics](../../metrics/program/program_referral_metrics.md) <br/>


##### Descendants
[dataflow_metrics_materialized.most_recent_program_referral_metrics](../dataflow_metrics_materialized/most_recent_program_referral_metrics.md) <br/>
|--[shared_metric_views.event_based_program_referrals](../shared_metric_views/event_based_program_referrals.md) <br/>
|----[dashboard_views.ftr_referrals_by_age_by_period](../dashboard_views/ftr_referrals_by_age_by_period.md) <br/>
|------[validation_views.ftr_referrals_comparison](../validation_views/ftr_referrals_comparison.md) <br/>
|------[validation_views.ftr_referrals_comparison_errors](../validation_views/ftr_referrals_comparison_errors.md) <br/>
|----[dashboard_views.ftr_referrals_by_gender_by_period](../dashboard_views/ftr_referrals_by_gender_by_period.md) <br/>
|------[validation_views.ftr_referrals_comparison](../validation_views/ftr_referrals_comparison.md) <br/>
|------[validation_views.ftr_referrals_comparison_errors](../validation_views/ftr_referrals_comparison_errors.md) <br/>
|----[dashboard_views.ftr_referrals_by_lsir_by_period](../dashboard_views/ftr_referrals_by_lsir_by_period.md) <br/>
|------[validation_views.ftr_referrals_comparison](../validation_views/ftr_referrals_comparison.md) <br/>
|------[validation_views.ftr_referrals_comparison_errors](../validation_views/ftr_referrals_comparison_errors.md) <br/>
|----[dashboard_views.ftr_referrals_by_month](../dashboard_views/ftr_referrals_by_month.md) <br/>
|----[dashboard_views.ftr_referrals_by_participation_status](../dashboard_views/ftr_referrals_by_participation_status.md) <br/>
|----[dashboard_views.ftr_referrals_by_period](../dashboard_views/ftr_referrals_by_period.md) <br/>
|----[dashboard_views.ftr_referrals_by_race_and_ethnicity_by_period](../dashboard_views/ftr_referrals_by_race_and_ethnicity_by_period.md) <br/>
|------[validation_views.ftr_referrals_comparison](../validation_views/ftr_referrals_comparison.md) <br/>
|------[validation_views.ftr_referrals_comparison_errors](../validation_views/ftr_referrals_comparison_errors.md) <br/>
