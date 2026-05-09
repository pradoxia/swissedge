# SwissEdge Diagnostics Overview

## Scanner Funnel Diagnostics

Track raw hits, parsed candidates, classified candidates, skipped unclassified, duplicates, evaluated count, created count, and errors.

## Routing Audits

Check whether form type and situation type route to the expected playbook and methodology status.

## Source Registry Diagnostics

Identify active sources without connectors, inactive sources with stale expectations, missing reliability fields, and sources producing no cases.

## Evidence Quality

Track whether evidence is official primary, official secondary, trusted external, external unverified, mixed, or unknown.

## Reliability

Measure source reliability, case usefulness, false positives, duplicate rates, stale items, and missing metadata.

## Noise Penalty

Flag sources or routes that produce frequent low-quality candidates.

## False Positives

Record cases that were discarded because they did not match methodology or lacked actionable evidence.

## False Negatives

Record missed opportunities discovered later, including why the source, routing rule, evidence parser, or methodology gate failed to surface them.

## Duplicate Detection

Detect same filing URL, same company/situation/date, same external URL, or repeated manual input.

## Missing Methodology

Flag ResearchCases without methodology status, playbook, checklist, or course reference.

## Missing Official Source

Flag external/manual cases without official evidence tasks or official-source status.

## Stale ResearchCases

Flag cases with no recent update, unresolved tasks, missed follow-up dates, or stale readiness.
