# SwissEdge Backend Files Deployment Script
# Run from repo root: .\scripts\deploy_backend_files.ps1

# Configuration
$VPS_HOST = "100.73.109.52"
$VPS_USER = "swdeploy"
$REMOTE_ROOT = "/opt/swissedge"
$BACKEND_SERVICE = "swissedge.service"

Write-Host "=== SwissEdge Backend Files Deployment ===" -ForegroundColor Cyan
Write-Host "Target: $VPS_USER@$VPS_HOST" -ForegroundColor Yellow

# Define files to deploy (allowlist)
$backendFiles = @(
    "backend/api/investment/router.py",
    "backend/models/investment.py",
    "backend/services/investment/evaluator.py",
    "backend/services/investment/routing_engine.py",
    "backend/services/investment/playbook_loader.py",
    "backend/services/investment/sec_detection.py",
    "backend/services/investment/detection_run_service.py",
    "backend/services/investment/detection_readiness.py",
    "backend/services/investment/document_package.py",
    "backend/services/investment/documentation_agent.py",
    "backend/services/investment/documentation_extraction.py",
    "backend/services/investment/documentation_sources.py",
    "backend/services/investment/knowledge_base.py",
    "backend/services/investment/promotion_readiness.py",
    "backend/services/investment/course_documentation_map.py",
    "backend/services/investment/skill_registry.py",
    "backend/services/investment/sec_false_detection_cleanup.py",
    "backend/services/investment/methodology_workspace.py",
    "backend/services/investment/resource_scout.py",
    "backend/services/investment/evidence_links.py",
    "backend/services/investment/intelligence_score.py",
    "backend/services/investment/intelligence_kpis.py",
    "backend/services/investment/fontana_report.py",
    "backend/services/investment/official_source_finder.py",
    "backend/services/investment/historical_analogues.py",
    "backend/services/investment/case_completion.py",
    "backend/services/investment/case_documentation.py",
    "backend/services/investment/case_activity.py",
    "backend/services/investment/sec_document_acquisition.py",
    "backend/services/investment/sec_company_facts.py",
    "backend/services/investment/dani_weber_metrics.py",
    "backend/services/investment/executive_review.py",
    "backend/services/investment/operational_view.py",
    "backend/services/investment/sources/sec_edgar.py",
    "backend/cli/__init__.py",
    "backend/cli/sec_edgar_detect.py",
    "backend/cli/sec_edgar_cleanup_false_detections.py",
    "backend/cli/special_situation_attach_methodology.py",
    "backend/cli/resource_scout_special_situation.py",
    "backend/services/observability/cron_reader.py",
    "scripts/run_sec_edgar_detection.sh",
    "backend/prompts/situation_evaluator_v2.txt",
    "backend/prompts/source_intelligence_preview.txt",
    "scripts/seed_investment_sources.py",
    "config/investment_sources.yaml",
    # Sprint 30 — Sales Items backend
    "backend/main.py",
    "backend/models/sales.py",
    "backend/api/marketplace/sales_items.py",
    "backend/db/migrations/env.py",
    "backend/db/migrations/versions/b2c3d4e5f6a7_add_sales_tables.py",
    # Phase 1A — Investment Research Platform persistence
    "backend/models/investment_research.py",
    "backend/models/source_intelligence.py",
    "backend/models/publishing.py",
    "backend/db/migrations/versions/c3d4e5f6a7b8_add_investment_research_tables.py",
    # Phase 1B — Research Cases service layer
    "backend/services/investment/research_cases.py",
    "backend/api/investment/research_cases.py",
    "backend/main.py",
    # Sprint C — V2 ResearchCase metadata additive migration (revision d4e5f6a7b8c9)
    "backend/db/migrations/versions/d4e5f6a7b8c9_add_researchcase_v2_metadata.py",
    # Sprint H — Agent Ops backend foundation (revision e5f6a7b8c9d0)
    "backend/models/agent_ops.py",
    "backend/services/agent_ops/__init__.py",
    "backend/services/agent_ops/service.py",
    "backend/services/agent_ops/activity_logger.py",
    "backend/api/agent_ops/__init__.py",
    "backend/api/agent_ops/router.py",
    "backend/db/migrations/versions/e5f6a7b8c9d0_add_agent_ops_tables.py",
    # SEC DetectionRun / Document Package / Promotion Readiness block
    "backend/db/migrations/versions/f6a7b8c9d0e1_add_detection_runs.py",
    # Documentation intake / extraction / knowledge sprint
    "backend/db/migrations/versions/g7b8c9d0e1f2_add_documentation_extraction_fields.py",
    "backend/db/migrations/versions/h8c9d0e1f2g3_add_research_document_body_text.py",
    "requirements.txt"
)

# Add course_index files if they exist
$courseIndexFiles = @()
if (Test-Path "course_index/playbooks") {
    $courseIndexFiles += Get-ChildItem "course_index/playbooks/*.md" -File | ForEach-Object { $_.FullName.Replace("$PWD\", "").Replace("\", "/") }
    # Add evaluation_schema.json from playbooks directory
    if (Test-Path "course_index/playbooks/evaluation_schema.json") {
        $courseIndexFiles += "course_index/playbooks/evaluation_schema.json"
    }
}

$allFiles = $backendFiles + $courseIndexFiles

$requiredBackendFiles = @(
    "backend/api/investment/router.py",
    "backend/api/investment/research_cases.py",
    "backend/services/investment/detection_readiness.py",
    "backend/services/investment/detection_run_service.py",
    "backend/services/investment/documentation_extraction.py",
    "backend/services/investment/documentation_sources.py",
    "backend/services/investment/knowledge_base.py",
    "backend/services/investment/course_documentation_map.py",
    "backend/services/investment/skill_registry.py",
    "backend/services/investment/documentation_agent.py",
    "backend/services/investment/sec_detection.py",
    "backend/services/investment/routing_engine.py",
    "backend/services/investment/sources/sec_edgar.py",
    "backend/db/migrations/versions/g7b8c9d0e1f2_add_documentation_extraction_fields.py",
    "requirements.txt"
)
$missingRequiredDeployEntries = $requiredBackendFiles | Where-Object { $backendFiles -notcontains $_ }
if ($missingRequiredDeployEntries.Count -gt 0) {
    Write-Host "ERROR: Required backend deployment files are not in the deploy allowlist:" -ForegroundColor Red
    $missingRequiredDeployEntries | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

$missingRequiredFiles = $requiredBackendFiles | Where-Object { -not (Test-Path $_) }
if ($missingRequiredFiles.Count -gt 0) {
    Write-Host "ERROR: Required backend deployment files are missing:" -ForegroundColor Red
    $missingRequiredFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

# Filter to only existing files
$filesToDeploy = $allFiles | Where-Object { Test-Path $_ }

if ($filesToDeploy.Count -eq 0) {
    Write-Host "ERROR: No files found to deploy" -ForegroundColor Red
    exit 1
}

Write-Host "`nFiles to deploy:" -ForegroundColor Green
$filesToDeploy | ForEach-Object { Write-Host "  - $_" }

# Step 1: Create deployment archive
Write-Host "`n[1/3] Creating backend deployment archive..." -ForegroundColor Green
if (Test-Path "backend_deploy.tar.gz") {
    Remove-Item "backend_deploy.tar.gz" -Force
}

# Create archive with all files preserving directory structure
tar -czf backend_deploy.tar.gz $filesToDeploy
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create archive" -ForegroundColor Red
    exit 1
}
Write-Host "Archive created: backend_deploy.tar.gz"

# Step 2: Copy archive to VPS
Write-Host "`n[2/3] Copying archive to VPS..." -ForegroundColor Green
scp backend_deploy.tar.gz "${VPS_USER}@${VPS_HOST}:/tmp/backend_deploy.tar.gz"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to copy archive" -ForegroundColor Red
    exit 1
}

# Step 3: Deploy on VPS (single SSH session)
# Note: PowerShell expands $REMOTE_ROOT, $timestamp, $BACKEND_SERVICE before sending.
# Bash-side variables ($BACKUP_DIR, $file) are escaped with backtick to prevent PS expansion.
Write-Host "`n[3/3] Deploying and restarting service..." -ForegroundColor Green
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

ssh "${VPS_USER}@${VPS_HOST}" @"
set -e

echo '--- Creating backup directory ---'
BACKUP_DIR=$REMOTE_ROOT/backup_$timestamp
sudo mkdir -p `$BACKUP_DIR

echo '--- Backing up existing files ---'
cd $REMOTE_ROOT
for file in backend/main.py backend/models/sales.py backend/models/investment.py backend/models/investment_research.py backend/models/source_intelligence.py backend/models/publishing.py backend/api/investment/router.py backend/api/investment/research_cases.py backend/api/marketplace/sales_items.py backend/services/investment/evaluator.py backend/services/investment/routing_engine.py backend/services/investment/playbook_loader.py backend/services/investment/sec_detection.py backend/services/investment/detection_run_service.py backend/services/investment/detection_readiness.py backend/services/investment/document_package.py backend/services/investment/documentation_agent.py backend/services/investment/documentation_extraction.py backend/services/investment/documentation_sources.py backend/services/investment/knowledge_base.py backend/services/investment/promotion_readiness.py backend/services/investment/course_documentation_map.py backend/services/investment/skill_registry.py backend/services/investment/sec_false_detection_cleanup.py backend/services/investment/methodology_workspace.py backend/services/investment/resource_scout.py backend/services/investment/evidence_links.py backend/services/investment/intelligence_score.py backend/services/investment/intelligence_kpis.py backend/services/investment/fontana_report.py backend/services/investment/official_source_finder.py backend/services/investment/historical_analogues.py backend/services/investment/case_completion.py backend/services/investment/case_documentation.py backend/services/investment/case_activity.py backend/services/investment/sec_document_acquisition.py backend/services/investment/sec_company_facts.py backend/services/investment/dani_weber_metrics.py backend/services/investment/executive_review.py backend/services/investment/operational_view.py backend/services/investment/research_cases.py backend/services/investment/sources/sec_edgar.py backend/cli/__init__.py backend/cli/sec_edgar_detect.py backend/cli/sec_edgar_cleanup_false_detections.py backend/cli/special_situation_attach_methodology.py backend/cli/resource_scout_special_situation.py scripts/run_sec_edgar_detection.sh backend/prompts/situation_evaluator_v2.txt backend/prompts/source_intelligence_preview.txt backend/db/migrations/env.py backend/db/migrations/versions/b2c3d4e5f6a7_add_sales_tables.py backend/db/migrations/versions/c3d4e5f6a7b8_add_investment_research_tables.py backend/db/migrations/versions/d4e5f6a7b8_add_researchcase_v2_metadata.py backend/db/migrations/versions/g7b8c9d0e1f2_add_documentation_extraction_fields.py backend/db/migrations/versions/h8c9d0e1f2g3_add_research_document_body_text.py backend/models/agent_ops.py backend/services/agent_ops/__init__.py backend/services/agent_ops/service.py backend/services/agent_ops/activity_logger.py backend/api/agent_ops/__init__.py backend/api/agent_ops/router.py backend/db/migrations/versions/e5f6a7b8c9d0_add_agent_ops_tables.py backend/db/migrations/versions/f6a7b8c9d0e1_add_detection_runs.py requirements.txt course_index/playbooks/*.md course_index/playbooks/evaluation_schema.json; do
    if [ -f `$file ]; then
        sudo mkdir -p `$BACKUP_DIR/`$(dirname `$file)
        sudo cp `$file `$BACKUP_DIR/`$file
        echo "  Backed up: `$file"
    fi
done

echo '--- Extracting new files ---'
sudo tar -xzf /tmp/backend_deploy.tar.gz -C $REMOTE_ROOT
sudo chown -R root:root $REMOTE_ROOT/backend $REMOTE_ROOT/course_index $REMOTE_ROOT/scripts $REMOTE_ROOT/config 2>/dev/null || true
rm /tmp/backend_deploy.tar.gz

echo '--- Restarting backend service ---'
sudo systemctl restart $BACKEND_SERVICE
sleep 3

echo '--- Health Check ---'
curl -i http://localhost:8000/api/health/ping 2>&1 | head -20

echo ''
echo '--- Service Status ---'
sudo systemctl status $BACKEND_SERVICE --no-pager

echo ''
echo '--- Backup Retention (keep 5 most recent backup_*) ---'
cd $REMOTE_ROOT
BACKUP_LIST=`$(ls -d backup_* 2>/dev/null | sort)
BACKUP_COUNT=`$(echo "`$BACKUP_LIST" | grep -c . 2>/dev/null || echo 0)
if [ "`$BACKUP_COUNT" -gt 5 ]; then
    TO_DELETE=`$(echo "`$BACKUP_LIST" | head -n `$(( BACKUP_COUNT - 5 )))
    for dir in `$TO_DELETE; do
        sudo rm -rf "$REMOTE_ROOT/`$dir"
        echo "  Removed old backup: `$dir"
    done
else
    echo "  `$BACKUP_COUNT backup(s) present - no cleanup needed"
fi
"@

# Cleanup local archive
Remove-Item "backend_deploy.tar.gz" -Force

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "Deployed $($filesToDeploy.Count) file(s)" -ForegroundColor Yellow
Write-Host "Backup created at: $REMOTE_ROOT/backup_$timestamp" -ForegroundColor Yellow
Write-Host "Backend should be accessible at http://${VPS_HOST}:8000" -ForegroundColor Yellow
