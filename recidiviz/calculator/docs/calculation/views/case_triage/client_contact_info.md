## case_triage.client_contact_info

Provides an association between people on supervision and their contact info.
 
Currently only generates data for Idaho and only contains email addresses.

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=case_triage&t=client_contact_info)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=case_triage&t=client_contact_info)
<br/>

#### Dependency Trees

##### Parentage
[case_triage.client_contact_info](../case_triage/client_contact_info.md) <br/>
|--us_id_raw_data_up_to_date_views.cis_phonenumber_latest ([Raw Data Doc](../../../ingest/us_id/raw_data/cis_phonenumber.md)) ([BQ Staging](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=us_id_raw_data_up_to_date_views&t=cis_phonenumber_latest)) ([BQ Prod](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=us_id_raw_data_up_to_date_views&t=cis_phonenumber_latest)) <br/>
|--us_id_raw_data_up_to_date_views.cis_personphonenumber_latest ([Raw Data Doc](../../../ingest/us_id/raw_data/cis_personphonenumber.md)) ([BQ Staging](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=us_id_raw_data_up_to_date_views&t=cis_personphonenumber_latest)) ([BQ Prod](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=us_id_raw_data_up_to_date_views&t=cis_personphonenumber_latest)) <br/>
|--us_id_raw_data_up_to_date_views.cis_personemailaddress_latest ([Raw Data Doc](../../../ingest/us_id/raw_data/cis_personemailaddress.md)) ([BQ Staging](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=us_id_raw_data_up_to_date_views&t=cis_personemailaddress_latest)) ([BQ Prod](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=us_id_raw_data_up_to_date_views&t=cis_personemailaddress_latest)) <br/>
|--us_id_raw_data_up_to_date_views.cis_offender_latest ([Raw Data Doc](../../../ingest/us_id/raw_data/cis_offender.md)) ([BQ Staging](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=us_id_raw_data_up_to_date_views&t=cis_offender_latest)) ([BQ Prod](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=us_id_raw_data_up_to_date_views&t=cis_offender_latest)) <br/>


##### Descendants
[case_triage.client_contact_info](../case_triage/client_contact_info.md) <br/>
|--[case_triage.etl_clients](../case_triage/etl_clients.md) <br/>
|----[case_triage.client_eligibility_criteria](../case_triage/client_eligibility_criteria.md) <br/>
|------[case_triage.etl_opportunities](../case_triage/etl_opportunities.md) <br/>
|--------[linestaff_data_validation.recommended_downgrades](../linestaff_data_validation/recommended_downgrades.md) <br/>
|----------[linestaff_data_validation.looker_dashboard](../linestaff_data_validation/looker_dashboard.md) <br/>
|--------[po_report_views.current_action_items_by_person](../po_report_views/current_action_items_by_person.md) <br/>
|----------[po_report_views.po_monthly_report_data](../po_report_views/po_monthly_report_data.md) <br/>
|------------[validation_views.po_report_avgs_per_district_state](../validation_views/po_report_avgs_per_district_state.md) <br/>
|------------[validation_views.po_report_clients](../validation_views/po_report_clients.md) <br/>
|------------[validation_views.po_report_distinct_by_officer_month](../validation_views/po_report_distinct_by_officer_month.md) <br/>
|------------[validation_views.po_report_missing_fields](../validation_views/po_report_missing_fields.md) <br/>
|------------[validation_views.po_report_missing_fields_errors](../validation_views/po_report_missing_fields_errors.md) <br/>
|--------[validation_views.case_triage_etl_freshness](../validation_views/case_triage_etl_freshness.md) <br/>
|----[case_triage.etl_client_events](../case_triage/etl_client_events.md) <br/>
|----[case_triage.etl_opportunities](../case_triage/etl_opportunities.md) <br/>
|------[linestaff_data_validation.recommended_downgrades](../linestaff_data_validation/recommended_downgrades.md) <br/>
|--------[linestaff_data_validation.looker_dashboard](../linestaff_data_validation/looker_dashboard.md) <br/>
|------[po_report_views.current_action_items_by_person](../po_report_views/current_action_items_by_person.md) <br/>
|--------[po_report_views.po_monthly_report_data](../po_report_views/po_monthly_report_data.md) <br/>
|----------[validation_views.po_report_avgs_per_district_state](../validation_views/po_report_avgs_per_district_state.md) <br/>
|----------[validation_views.po_report_clients](../validation_views/po_report_clients.md) <br/>
|----------[validation_views.po_report_distinct_by_officer_month](../validation_views/po_report_distinct_by_officer_month.md) <br/>
|----------[validation_views.po_report_missing_fields](../validation_views/po_report_missing_fields.md) <br/>
|----------[validation_views.po_report_missing_fields_errors](../validation_views/po_report_missing_fields_errors.md) <br/>
|------[validation_views.case_triage_etl_freshness](../validation_views/case_triage_etl_freshness.md) <br/>
|----[experiments.case_triage_metrics](../experiments/case_triage_metrics.md) <br/>
|----[po_report_views.current_action_items_by_person](../po_report_views/current_action_items_by_person.md) <br/>
|------[po_report_views.po_monthly_report_data](../po_report_views/po_monthly_report_data.md) <br/>
|--------[validation_views.po_report_avgs_per_district_state](../validation_views/po_report_avgs_per_district_state.md) <br/>
|--------[validation_views.po_report_clients](../validation_views/po_report_clients.md) <br/>
|--------[validation_views.po_report_distinct_by_officer_month](../validation_views/po_report_distinct_by_officer_month.md) <br/>
|--------[validation_views.po_report_missing_fields](../validation_views/po_report_missing_fields.md) <br/>
|--------[validation_views.po_report_missing_fields_errors](../validation_views/po_report_missing_fields_errors.md) <br/>
|----[validation_views.case_triage_etl_freshness](../validation_views/case_triage_etl_freshness.md) <br/>
|----[validation_views.case_triage_f2f_contact_freshness](../validation_views/case_triage_f2f_contact_freshness.md) <br/>
|----[validation_views.case_triage_risk_assessment_freshness](../validation_views/case_triage_risk_assessment_freshness.md) <br/>
|----[validation_views.most_recent_assessment_date_by_person_by_state_comparison](../validation_views/most_recent_assessment_date_by_person_by_state_comparison.md) <br/>
|----[validation_views.most_recent_assessment_date_by_person_by_state_comparison_errors](../validation_views/most_recent_assessment_date_by_person_by_state_comparison_errors.md) <br/>
|----[validation_views.most_recent_assessment_score_by_person_by_state_comparison](../validation_views/most_recent_assessment_score_by_person_by_state_comparison.md) <br/>
|----[validation_views.most_recent_assessment_score_by_person_by_state_comparison_errors](../validation_views/most_recent_assessment_score_by_person_by_state_comparison_errors.md) <br/>
|----[validation_views.most_recent_face_to_face_contact_date_by_person_by_state_comparison](../validation_views/most_recent_face_to_face_contact_date_by_person_by_state_comparison.md) <br/>
|----[validation_views.most_recent_face_to_face_contact_date_by_person_by_state_comparison_errors](../validation_views/most_recent_face_to_face_contact_date_by_person_by_state_comparison_errors.md) <br/>
