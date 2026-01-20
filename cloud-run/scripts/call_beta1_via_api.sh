#!/bin/bash
#
# Call Beta1 scan via HTTP API endpoint
# Usage: ./call_beta1_via_api.sh [api_url] [max_results]
#
# Examples:
#   ./call_beta1_via_api.sh https://mcp-backend-xxxxx.run.app 11
#   ./call_beta1_via_api.sh http://localhost:8080
#   ./call_beta1_via_api.sh  # Uses localhost:8080 by default

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
API_URL="${1:-http://localhost:8080}"
MAX_RESULTS="${2:-11}"
UNIVERSE="beta1"

echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                     🚀 BETA1 SCAN VIA API${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "${GREEN}Configuration:${NC}"
echo -e "  API URL:      ${API_URL}"
echo -e "  Universe:     ${UNIVERSE}"
echo -e "  Max Results:  ${MAX_RESULTS}\n"

# Test API connectivity
echo -e "${YELLOW}⏳ Testing API connectivity...${NC}"
if ! curl -s -f "${API_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ API not responding at ${API_URL}${NC}"
    echo -e "\n${YELLOW}Troubleshooting:${NC}"
    echo "  1. Is the API running? (Check with: curl ${API_URL}/health)"
    echo "  2. Is the URL correct?"
    echo "  3. Check logs: gcloud run services logs read mcp-backend --region=us-central1"
    exit 1
fi
echo -e "${GREEN}✓ API is responsive${NC}\n"

# Call API
echo -e "${YELLOW}⏳ Calling scan endpoint...${NC}"
echo -e "${YELLOW}   Scanning Beta1 universe (This may take 30-90 seconds)${NC}\n"

RESPONSE=$(curl -s -X POST "${API_URL}/api/scan" \
    -H "Content-Type: application/json" \
    -d "{
        \"universe\": \"${UNIVERSE}\",
        \"max_results\": ${MAX_RESULTS}
    }")

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}✗ API request failed (curl exit code: $EXIT_CODE)${NC}"
    echo -e "\n${YELLOW}Response:${NC}"
    echo "${RESPONSE}"
    exit 1
fi

# Parse response
STATUS=$(echo "$RESPONSE" | jq -r '.status // "success"' 2>/dev/null)
TOTAL_SCANNED=$(echo "$RESPONSE" | jq -r '.total_scanned // "unknown"' 2>/dev/null)
QUALIFIED_COUNT=$(echo "$RESPONSE" | jq '[.qualified_trades[]? // empty] | length' 2>/dev/null)

if [ "$STATUS" = "error" ] || [ "$TOTAL_SCANNED" = "null" ]; then
    echo -e "${RED}✗ API returned an error${NC}"
    echo -e "\n${YELLOW}Response:${NC}"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Scan complete!${NC}\n"

# Display results
echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                          SCAN RESULTS${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "${GREEN}Summary:${NC}"
echo -e "  Total scanned:      ${TOTAL_SCANNED}"
echo -e "  Qualified trades:   ${QUALIFIED_COUNT}"

if [ "$QUALIFIED_COUNT" -gt 0 ]; then
    echo -e "\n${GREEN}Top Qualified Trades:${NC}\n"

    # Extract and display top trades
    echo "$RESPONSE" | jq -r '.qualified_trades[] |
        "\(.symbol | ascii_upcase) | Score: \(.quality_score | round)/100 | \(.primary_signal) | \(.current_price)"' | \
        head -10 | \
        awk -F'|' '{
            printf "  %-8s | Score: %s | %-4s | Price: $%s\n", $1, $2, $4, $5
        }' | \
        nl -w 2 -s '. '
else
    echo -e "\n${YELLOW}(No qualified trades found in this scan)${NC}"
fi

# Save results to file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="beta1_scan_${TIMESTAMP}.json"
echo "$RESPONSE" | jq '.' > "$OUTPUT_FILE"

echo -e "\n${GREEN}✓ Results saved to: ${OUTPUT_FILE}${NC}"

# View on Firebase option
echo -e "\n${YELLOW}To view results in Firebase:${NC}"
echo -e "  https://console.firebase.google.com/project/ttb-lang1/firestore"
echo -e "  → Collections → scans → beta1_latest\n"

# Show next steps
echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Beta1 scan complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}Next steps:${NC}"
echo "  1. View results: cat ${OUTPUT_FILE}"
echo "  2. Parse with jq: cat ${OUTPUT_FILE} | jq '.qualified_trades | .[] | {symbol, score: .quality_score}'"
echo "  3. Save to Firebase: python3 run_beta1_scan.py"
echo ""
