#!/usr/bin/env bash
# =============================================================================
# Agentic SOC — GCP Project Setup Script
#
# One-shot script that sets up the entire GCP infrastructure:
#   1. Creates/selects GCP project
#   2. Links billing account
#   3. Enables required APIs
#   4. Configures Artifact Registry
#   5. Builds & pushes Docker images
#   6. Initializes Terraform state bucket
#   7. Runs Terraform to create all resources
#   8. Onboards the NFR test client
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (gcloud auth login)
#   - docker installed and running
#   - terraform installed (>= 1.7)
#   - A GCP billing account
#
# Usage:
#   chmod +x scripts/setup_gcp.sh
#   ./scripts/setup_gcp.sh --project my-partner-project --region us-central1
#
#   # Skip steps you've already done:
#   ./scripts/setup_gcp.sh --project my-partner-project --skip-project-create --skip-billing
#
# =============================================================================
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
step()    { echo -e "\n${GREEN}━━━ Step $1: $2 ━━━${NC}"; }

# ── Default values ──────────────────────────────────────────────────────────
PROJECT_ID=""
REGION="us-central1"
ENVIRONMENT="dev"
BILLING_ACCOUNT=""
SKIP_PROJECT_CREATE=false
SKIP_BILLING=false
SKIP_DOCKER=false
SKIP_TERRAFORM=false
SKIP_ONBOARD=false
DRY_RUN=false

# ── Parse args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)          PROJECT_ID="$2"; shift 2 ;;
        --region)           REGION="$2"; shift 2 ;;
        --environment)      ENVIRONMENT="$2"; shift 2 ;;
        --billing-account)  BILLING_ACCOUNT="$2"; shift 2 ;;
        --skip-project-create) SKIP_PROJECT_CREATE=true; shift ;;
        --skip-billing)     SKIP_BILLING=true; shift ;;
        --skip-docker)      SKIP_DOCKER=true; shift ;;
        --skip-terraform)   SKIP_TERRAFORM=true; shift ;;
        --skip-onboard)     SKIP_ONBOARD=true; shift ;;
        --dry-run)          DRY_RUN=true; shift ;;
        -h|--help)
            echo "Usage: $0 --project PROJECT_ID [--region REGION] [--environment ENV]"
            echo ""
            echo "Options:"
            echo "  --project PROJECT_ID        GCP project ID (required)"
            echo "  --region REGION             GCP region (default: us-central1)"
            echo "  --environment ENV           Environment: dev|staging|prod (default: dev)"
            echo "  --billing-account ID        Billing account ID (auto-detected if one exists)"
            echo "  --skip-project-create       Skip GCP project creation (already exists)"
            echo "  --skip-billing              Skip billing account linking"
            echo "  --skip-docker               Skip Docker build & push"
            echo "  --skip-terraform            Skip Terraform init & apply"
            echo "  --skip-onboard              Skip NFR client onboarding"
            echo "  --dry-run                   Print what would be done, don't execute"
            exit 0
            ;;
        *) error "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$PROJECT_ID" ]]; then
    error "--project is required"
    exit 1
fi

# ── Derived values ──────────────────────────────────────────────────────────
AR_REPO="${REGION}-docker.pkg.dev/${PROJECT_ID}/agentic-soc"
TFSTATE_BUCKET="${PROJECT_ID}-tfstate"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

info "Project:     ${PROJECT_ID}"
info "Region:      ${REGION}"
info "Environment: ${ENVIRONMENT}"
info "Project root: ${PROJECT_ROOT}"
info ""

if $DRY_RUN; then
    warn "DRY RUN — no changes will be made"
    echo ""
fi

# ── Helper ──────────────────────────────────────────────────────────────────
run() {
    if $DRY_RUN; then
        echo "  [DRY RUN] $*"
    else
        "$@"
    fi
}

# =============================================================================
# Step 1: Create GCP Project
# =============================================================================
step 1 "GCP Project Setup"

if $SKIP_PROJECT_CREATE; then
    info "Skipping project creation (--skip-project-create)"
else
    if gcloud projects describe "$PROJECT_ID" &>/dev/null; then
        info "Project '$PROJECT_ID' already exists"
    else
        info "Creating project: $PROJECT_ID"
        run gcloud projects create "$PROJECT_ID" --name="Agentic SOC"
    fi
fi

run gcloud config set project "$PROJECT_ID"
success "Project set: $PROJECT_ID"

# =============================================================================
# Step 2: Link Billing Account
# =============================================================================
step 2 "Billing Account"

if $SKIP_BILLING; then
    info "Skipping billing (--skip-billing)"
else
    if [[ -z "$BILLING_ACCOUNT" ]]; then
        BILLING_ACCOUNT=$(gcloud billing accounts list --format='value(ACCOUNT_ID)' --filter='open=true' | head -1)
        if [[ -z "$BILLING_ACCOUNT" ]]; then
            error "No billing account found. Use --billing-account to specify one."
            exit 1
        fi
        info "Auto-detected billing account: $BILLING_ACCOUNT"
    fi
    run gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT"
    success "Billing linked: $BILLING_ACCOUNT"
fi

# =============================================================================
# Step 3: Enable APIs
# =============================================================================
step 3 "Enable APIs"

APIS=(
    aiplatform.googleapis.com
    run.googleapis.com
    firestore.googleapis.com
    secretmanager.googleapis.com
    logging.googleapis.com
    cloudtrace.googleapis.com
    iam.googleapis.com
    iamcredentials.googleapis.com
    cloudresourcemanager.googleapis.com
    artifactregistry.googleapis.com
    cloudbuild.googleapis.com
    monitoring.googleapis.com
    modelarmor.googleapis.com
)

info "Enabling ${#APIS[@]} APIs (this may take a few minutes)..."
for api in "${APIS[@]}"; do
    run gcloud services enable "$api" --project="$PROJECT_ID" &
done
wait
success "All APIs enabled"

# =============================================================================
# Step 4: Create Artifact Registry
# =============================================================================
step 4 "Artifact Registry"

if gcloud artifacts repositories describe agentic-soc --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    info "Artifact Registry 'agentic-soc' already exists"
else
    info "Creating Artifact Registry repository..."
    run gcloud artifacts repositories create agentic-soc \
        --repository-format=docker \
        --location="$REGION" \
        --description="Agentic SOC Docker images" \
        --project="$PROJECT_ID"
fi

# Configure Docker auth for the registry
run gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
success "Artifact Registry ready: ${AR_REPO}"

# =============================================================================
# Step 5: Build & Push Docker Images
# =============================================================================
step 5 "Docker Build & Push"

if $SKIP_DOCKER; then
    info "Skipping Docker build (--skip-docker)"
else
    cd "$PROJECT_ROOT"

    info "Building MCP Gateway image..."
    run docker build -f proxy/Dockerfile -t "${AR_REPO}/mcp-gateway:latest" .

    info "Building HITL Backend image..."
    run docker build -f ui/hitl_dashboard/Dockerfile -t "${AR_REPO}/hitl-backend:latest" .

    info "Pushing images to Artifact Registry..."
    run docker push "${AR_REPO}/mcp-gateway:latest"
    run docker push "${AR_REPO}/hitl-backend:latest"

    success "Images pushed to ${AR_REPO}"
fi

# =============================================================================
# Step 6: Create Terraform State Bucket
# =============================================================================
step 6 "Terraform State Bucket"

if gcloud storage buckets describe "gs://${TFSTATE_BUCKET}" &>/dev/null 2>&1; then
    info "Terraform state bucket already exists: ${TFSTATE_BUCKET}"
else
    info "Creating Terraform state bucket: ${TFSTATE_BUCKET}"
    run gcloud storage buckets create "gs://${TFSTATE_BUCKET}" \
        --location="$REGION" \
        --uniform-bucket-level-access \
        --project="$PROJECT_ID"
fi

success "Terraform state: gs://${TFSTATE_BUCKET}/agentic-soc/terraform/state"

# =============================================================================
# Step 7: Generate terraform.tfvars
# =============================================================================
step 7 "Generate Terraform Config"

TFVARS_PATH="${PROJECT_ROOT}/infra/terraform/terraform.tfvars"

if [[ -f "$TFVARS_PATH" ]]; then
    warn "terraform.tfvars already exists — not overwriting"
    info "Delete it manually if you want to regenerate"
else
    info "Generating terraform.tfvars..."
    if ! $DRY_RUN; then
        cat > "$TFVARS_PATH" <<EOF
# Auto-generated by setup_gcp.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)
# NEVER commit this file to git.

partner_project_id = "${PROJECT_ID}"
region             = "${REGION}"
chronicle_region   = "us"
environment        = "${ENVIRONMENT}"

mcp_gateway_image  = "${AR_REPO}/mcp-gateway:latest"
hitl_backend_image = "${AR_REPO}/hitl-backend:latest"

model_armor_enabled = true
EOF
    fi
    success "terraform.tfvars generated"
fi

# =============================================================================
# Step 8: Terraform Init & Apply
# =============================================================================
step 8 "Terraform Deploy"

if $SKIP_TERRAFORM; then
    info "Skipping Terraform (--skip-terraform)"
else
    cd "${PROJECT_ROOT}/infra/terraform"

    info "Initializing Terraform..."
    run terraform init \
        -backend-config="bucket=${TFSTATE_BUCKET}" \
        -reconfigure

    info "Planning infrastructure..."
    run terraform plan -out=tfplan

    echo ""
    if $DRY_RUN; then
        info "[DRY RUN] Would run: terraform apply tfplan"
    else
        echo -e "${YELLOW}Review the plan above. Apply? (yes/no)${NC}"
        read -r CONFIRM
        if [[ "$CONFIRM" == "yes" ]]; then
            terraform apply tfplan
            success "Terraform apply complete"
        else
            warn "Terraform apply skipped by user"
        fi
    fi

    # Capture outputs
    if ! $DRY_RUN && [[ -f terraform.tfstate ]] || terraform state list &>/dev/null 2>&1; then
        GATEWAY_URL=$(terraform output -raw mcp_gateway_url 2>/dev/null || echo "")
        HITL_URL=$(terraform output -raw hitl_dashboard_url 2>/dev/null || echo "")

        if [[ -n "$GATEWAY_URL" ]]; then
            success "MCP Gateway:    $GATEWAY_URL"
            success "HITL Dashboard: $HITL_URL"
        fi
    fi

    cd "$PROJECT_ROOT"
fi

# =============================================================================
# Step 9: Generate .env
# =============================================================================
step 9 "Generate .env"

ENV_PATH="${PROJECT_ROOT}/.env"

if [[ -f "$ENV_PATH" ]]; then
    warn ".env already exists — not overwriting"
else
    info "Generating .env from template..."
    GATEWAY_URL=${GATEWAY_URL:-"http://localhost:8080"}
    if ! $DRY_RUN; then
        cat > "$ENV_PATH" <<EOF
# Auto-generated by setup_gcp.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)
PARTNER_PROJECT_ID=${PROJECT_ID}
PARTNER_REGION=${REGION}
VERTEX_AI_LOCATION=${REGION}
GEMINI_FLASH_MODEL=gemini-2.5-flash
GEMINI_PRO_MODEL=gemini-2.5-pro
MCP_GATEWAY_URL=${GATEWAY_URL}
MCP_GATEWAY_PORT=8080
FIRESTORE_DATABASE=(default)
SECRET_MANAGER_PREFIX=agentic-soc
HITL_BACKEND_PORT=8081
LOG_LEVEL=INFO
MODEL_ARMOR_ENABLED=true
MODEL_ARMOR_TEMPLATE_ID=agentic-soc-${ENVIRONMENT}
DEV_MODE=false
NFR_CLIENT_ID=nfr-partner-client
EOF
    fi
    success ".env generated"
fi

# =============================================================================
# Step 10: Onboard NFR Client (optional)
# =============================================================================
step 10 "NFR Client Onboarding"

if $SKIP_ONBOARD; then
    info "Skipping onboarding (--skip-onboard)"
else
    NFR_CONFIG="${PROJECT_ROOT}/config/clients/nfr-partner-client.yaml"

    if [[ ! -f "$NFR_CONFIG" ]]; then
        warn "NFR config not found: $NFR_CONFIG"
        info "Copy config/clients/client_template.yaml and fill in your Chronicle NFR values"
    else
        # Check if the config has placeholder values
        if grep -q "REPLACE_ME" "$NFR_CONFIG"; then
            warn "NFR config has placeholder values. Edit $NFR_CONFIG with real values, then run:"
            info "  python scripts/onboard_client.py --config $NFR_CONFIG --partner-project $PROJECT_ID"
        else
            info "Onboarding NFR client..."
            GATEWAY_URL=${GATEWAY_URL:-""}
            if [[ -n "$GATEWAY_URL" ]]; then
                run python scripts/onboard_client.py \
                    --config "$NFR_CONFIG" \
                    --partner-project "$PROJECT_ID" \
                    --gateway-url "$GATEWAY_URL"
            else
                run python scripts/onboard_client.py \
                    --config "$NFR_CONFIG" \
                    --partner-project "$PROJECT_ID" \
                    --skip-connectivity
            fi
        fi
    fi
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Agentic SOC — Setup Complete${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Project:          ${PROJECT_ID}"
echo "  Region:           ${REGION}"
echo "  Environment:      ${ENVIRONMENT}"
echo "  Artifact Registry: ${AR_REPO}"
echo "  TF State:         gs://${TFSTATE_BUCKET}/agentic-soc/terraform/state"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Edit config/clients/nfr-partner-client.yaml with your Chronicle NFR values"
echo "  2. Run: python scripts/onboard_client.py --config config/clients/nfr-partner-client.yaml"
echo "  3. Test: curl \${MCP_GATEWAY_URL}/health"
echo "  4. Deploy agents: python scripts/deploy_agent.py --project ${PROJECT_ID} --gateway-url \${MCP_GATEWAY_URL}"
echo ""
echo -e "${BLUE}Local development:${NC}"
echo "  python -m agentic-soc serve                    # Start gateway + HITL locally"
echo "  streamlit run ui/hitl_dashboard/frontend/app.py # Start HITL frontend"
echo ""
