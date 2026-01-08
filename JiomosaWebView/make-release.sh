#!/bin/bash

# JiomosaWebView Release Version Script
# This script helps create a new release version with automated checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current version from build.gradle
CURRENT_VERSION=$(grep "versionName" app/build.gradle | awk '{print $2}' | tr -d '"')
CURRENT_CODE=$(grep "versionCode" app/build.gradle | awk '{print $2}')

echo -e "${BLUE}=== JiomosaWebView Release Version Creator ===${NC}"
echo -e "Current version: ${GREEN}$CURRENT_VERSION${NC} (code: $CURRENT_CODE)"
echo ""

# Ask for version type
echo "Select version bump type:"
echo "1) PATCH (bug fixes)        - e.g., 1.0.0 → 1.0.1"
echo "2) MINOR (new features)     - e.g., 1.0.0 → 1.1.0"
echo "3) MAJOR (breaking changes) - e.g., 1.0.0 → 2.0.0"
echo "4) Custom version"
echo ""
read -p "Enter choice [1-4]: " choice

# Parse current version
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Calculate new version
case $choice in
    1)
        NEW_PATCH=$((PATCH + 1))
        NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"
        VERSION_TYPE="PATCH"
        ;;
    2)
        NEW_MINOR=$((MINOR + 1))
        NEW_VERSION="$MAJOR.$NEW_MINOR.0"
        VERSION_TYPE="MINOR"
        ;;
    3)
        NEW_MAJOR=$((MAJOR + 1))
        NEW_VERSION="$NEW_MAJOR.0.0"
        VERSION_TYPE="MAJOR"
        ;;
    4)
        read -p "Enter new version (e.g., 1.2.0): " NEW_VERSION
        VERSION_TYPE="CUSTOM"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

NEW_CODE=$((CURRENT_CODE + 1))

echo ""
echo -e "New version: ${GREEN}$NEW_VERSION${NC} (code: $NEW_CODE)"
echo ""

# Confirm
read -p "Proceed with this version? [y/N]: " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${BLUE}Step 1: Running Security & Code Review...${NC}"

# Check for common security issues
echo "  → Checking for hardcoded secrets..."
if grep -r "password\|secret\|api_key\|token" app/src/ --include="*.kt" --include="*.java" 2>/dev/null | grep -v "// " | grep -v "Toast\|Log\|TAG\|SecureRandom"; then
    echo -e "${YELLOW}  ⚠ Warning: Potential secrets found in code${NC}"
fi

echo "  → Checking for debug logging in release..."
DEBUG_LOGS=$(grep -r "Log\." app/src/ --include="*.kt" --include="*.java" 2>/dev/null | wc -l || echo "0")
if [ "$DEBUG_LOGS" -gt 50 ]; then
    echo -e "${YELLOW}  ⚠ Warning: $DEBUG_LOGS debug log statements found${NC}"
fi

echo "  → Checking AndroidManifest permissions..."
PERMISSION_COUNT=$(grep "uses-permission" app/src/main/AndroidManifest.xml | wc -l)
echo -e "  ℹ $PERMISSION_COUNT permissions declared"

echo "  → Checking ProGuard configuration..."
if [ -f "app/proguard-rules.pro" ]; then
    echo -e "${GREEN}  ✓ ProGuard rules file exists${NC}"
else
    echo -e "${YELLOW}  ⚠ Warning: No ProGuard rules file${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Updating Version Numbers...${NC}"

# Update build.gradle
sed -i.bak "s/versionCode $CURRENT_CODE/versionCode $NEW_CODE/" app/build.gradle
sed -i.bak "s/versionName \"$CURRENT_VERSION\"/versionName \"$NEW_VERSION\"/" app/build.gradle
rm app/build.gradle.bak

echo -e "${GREEN}  ✓ Updated app/build.gradle${NC}"

# Add entry to VERSION.md
DATE=$(date +"%Y-%m-%d")
VERSION_ENTRY="## Version $NEW_VERSION ($DATE) - $VERSION_TYPE Release\n\n### Changes\n- [Add changes here]\n\n### Security\n- No security issues detected\n\n### Known Issues\n- None\n\n---\n\n"

# Insert after first heading
sed -i.bak "s/# JiomosaWebView Version History/# JiomosaWebView Version History\n\n$VERSION_ENTRY/" VERSION.md
rm VERSION.md.bak

echo -e "${GREEN}  ✓ Updated VERSION.md${NC}"

echo ""
echo -e "${BLUE}Step 3: Building Release APK...${NC}"

# Clean build
./gradlew clean

# Build release
if ./gradlew assembleRelease; then
    echo -e "${GREEN}  ✓ Release build successful${NC}"
    
    # Show APK location
    APK_PATH="app/build/outputs/apk/release/app-release-unsigned.apk"
    if [ -f "$APK_PATH" ]; then
        APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
        echo -e "  📦 APK: $APK_PATH ($APK_SIZE)"
    fi
else
    echo -e "${RED}  ✗ Release build failed${NC}"
    echo "  Rolling back version changes..."
    sed -i.bak "s/versionCode $NEW_CODE/versionCode $CURRENT_CODE/" app/build.gradle
    sed -i.bak "s/versionName \"$NEW_VERSION\"/versionName \"$CURRENT_VERSION\"/" app/build.gradle
    rm app/build.gradle.bak
    exit 1
fi

echo ""
echo -e "${GREEN}=== Release Version $NEW_VERSION Created Successfully ===${NC}"
echo ""
echo "Next steps:"
echo "1. Edit VERSION.md to document changes for this release"
echo "2. Sign the APK: ./build-sign-install.sh (if you have keystore)"
echo "3. Test the release build thoroughly"
echo "4. Commit the version changes: git add . && git commit -m 'Release v$NEW_VERSION'"
echo "5. Tag the release: git tag v$NEW_VERSION"
echo ""
