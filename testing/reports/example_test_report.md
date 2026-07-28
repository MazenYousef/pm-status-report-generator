# Blackbox Test Report
_Generated 2026-07-28T00:46:30_

## Executive Summary
Overall status: **PASS**. 57 test(s) ran in 16.60s — 51 passed, 0 failed, 6 skipped.

## Results
| Test | Status | Duration (s) | Note |
|---|---|---|---|
| testcases.test_cli_live::test_dry_run_live_github | SKIPPED | 0.00 | GITHUB_TOKEN/GITHUB_REPO not configured with real values |
| testcases.test_cli_live::test_dry_run_live_jira | SKIPPED | 0.00 | JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN not configured with real values |
| testcases.test_cli_live::test_sample_real_claude_call[github-sample] | SKIPPED | 0.00 | ANTHROPIC_API_KEY not configured with a real value |
| testcases.test_cli_live::test_sample_real_claude_call[jira-sample] | SKIPPED | 0.00 | ANTHROPIC_API_KEY not configured with a real value |
| testcases.test_cli_live::test_full_live_run_github | SKIPPED | 0.00 | requires real GitHub creds + ANTHROPIC_API_KEY |
| testcases.test_cli_live::test_full_live_run_jira | SKIPPED | 0.00 | requires real Jira creds + ANTHROPIC_API_KEY |
| testcases.test_cli_offline::test_sample_dry_run[tracker-unset] | PASSED | 2.35 |  |
| testcases.test_cli_offline::test_sample_dry_run[tracker-github] | PASSED | 1.53 |  |
| testcases.test_cli_offline::test_sample_dry_run[tracker-jira] | PASSED | 1.57 |  |
| testcases.test_cli_offline::test_dry_run_without_sample_is_prompt_preview_only | PASSED | 1.55 |  |
| testcases.test_config::test_defaults_when_env_unset | PASSED | 0.00 |  |
| testcases.test_config::test_issue_tracker_is_lowercased_and_stripped | PASSED | 0.00 |  |
| testcases.test_config::test_lookback_days_parsed_as_int | PASSED | 0.00 |  |
| testcases.test_config::test_jira_base_url_trailing_slash_stripped | PASSED | 0.00 |  |
| testcases.test_github_fetcher::test_missing_credentials_raises_before_any_request | PASSED | 0.00 |  |
| testcases.test_github_fetcher::test_missing_repo_only_still_raises | PASSED | 0.00 |  |
| testcases.test_jira_fetcher.TestBuildJql::test_full_query_with_project_and_labels | PASSED | 0.00 |  |
| testcases.test_jira_fetcher.TestBuildJql::test_closed_state_no_project_no_labels | PASSED | 0.00 |  |
| testcases.test_jira_fetcher.TestBuildJql::test_all_state_omits_status_clause | PASSED | 0.00 |  |
| testcases.test_jira_fetcher.TestAdfToText::test_multiple_paragraphs_are_newline_separated | PASSED | 0.00 |  |
| testcases.test_jira_fetcher.TestAdfToText::test_nested_list_item_flattened | PASSED | 0.00 |  |
| testcases.test_jira_fetcher.TestAdfToText::test_none_and_empty_are_safe | PASSED | 0.00 |  |
| testcases.test_jira_fetcher::test_fetch_issues_maps_mocked_response_to_expected_shape | PASSED | 0.00 |  |
| testcases.test_jira_fetcher::test_missing_credentials_raises_before_any_request[all-missing] | PASSED | 0.00 |  |
| testcases.test_jira_fetcher::test_missing_credentials_raises_before_any_request[email-and-token-missing] | PASSED | 0.00 |  |
| testcases.test_jira_fetcher::test_missing_credentials_raises_before_any_request[token-missing] | PASSED | 0.00 |  |
| testcases.test_output_naming::test_filenames_match_date_timestamp_convention | PASSED | 1.66 |  |
| testcases.test_output_naming::test_repeated_runs_do_not_overwrite_each_other | PASSED | 4.37 |  |
| testcases.test_pdf_generation::test_no_template_pdf_contains_all_sections | PASSED | 1.54 |  |
| testcases.test_pdf_generation::test_with_template_pdf_contains_branding_and_sections | PASSED | 1.54 |  |
| testcases.test_pdf_generation::test_missing_soffice_raises_clear_error | PASSED | 0.00 |  |
| testcases.test_pdf_generation::test_malformed_sections_do_not_crash_rendering[missing-sections] | PASSED | 0.01 |  |
| testcases.test_pdf_generation::test_malformed_sections_do_not_crash_rendering[empty-section-body] | PASSED | 0.01 |  |
| testcases.test_project_structure::test_required_file_exists[sample_data/github_sample_issues.json] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[sample_data/jira_sample_issues.json] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[reports/example_output_github.md] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[reports/example_output_jira.md] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[templates/README.md] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[.env.example] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[src/main.py] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[src/config.py] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[src/fetch_issues.py] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[src/fetch_jira_issues.py] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[src/generate_report.py] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_required_file_exists[src/generate_pdf.py] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_dependency_importable[anthropic] | PASSED | 0.35 |  |
| testcases.test_project_structure::test_dependency_importable[requests] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_dependency_importable[dotenv] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_dependency_importable[docx] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_dependency_importable[docxtpl] | PASSED | 0.00 |  |
| testcases.test_project_structure::test_dependency_importable[docxcompose] | PASSED | 0.00 |  |
| testcases.test_workflow_config::test_workflow_file_exists | PASSED | 0.00 |  |
| testcases.test_workflow_config::test_workflow_contains_expected_substring[cron:] | PASSED | 0.00 |  |
| testcases.test_workflow_config::test_workflow_contains_expected_substring[workflow_dispatch] | PASSED | 0.00 |  |
| testcases.test_workflow_config::test_workflow_contains_expected_substring[Install LibreOffice] | PASSED | 0.00 |  |
| testcases.test_workflow_config::test_workflow_contains_expected_substring[python src/main.py] | PASSED | 0.00 |  |
| testcases.test_workflow_config::test_workflow_contains_expected_substring[git add reports/] | PASSED | 0.00 |  |
