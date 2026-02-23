#!/bin/bash
# Scan all workflow files to extract secrets and variables

WORKFLOWS_DIR="../.forgejo/workflows"
SECRETS_FILE="required-secrets.txt"
VARS_FILE="required-vars.txt"

echo "Scanning workflows for secrets and variables..."

# Extract secrets (lines with ${{ secrets.XXX }})
grep -rh '\${{ secrets\.' "$WORKFLOWS_DIR" | \
  grep -o 'secrets\.[A-Z_0-9]*' | \
  sed 's/secrets\.//' | \
  sort -u > "$SECRETS_FILE"

# Extract variables (lines with ${{ vars.XXX }})
grep -rh '\${{ vars\.' "$WORKFLOWS_DIR" | \
  grep -o 'vars\.[A-Z_0-9]*' | \
  sed 's/vars\.//' | \
  sort -u > "$VARS_FILE"

echo ""
echo "Found $(wc -l < "$SECRETS_FILE") unique secrets:"
cat "$SECRETS_FILE"

echo ""
echo "Found $(wc -l < "$VARS_FILE") unique variables:"
cat "$VARS_FILE"

echo ""
echo "Lists saved to:"
echo "  - $SECRETS_FILE"
echo "  - $VARS_FILE"
