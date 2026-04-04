#!/bin/bash

# Script to verify OpenSpace installation and functionality

echo "🔍 Verifying OpenSpace Installation..."

# Check if openspace-mcp is available
echo "Checking openspace-mcp..."
if command -v openspace-mcp &> /dev/null; then
    echo "✅ openspace-mcp is available"
    openspace-mcp --help | head -5
else
    echo "❌ openspace-mcp not found"
    exit 1
fi

# Check if openspace CLI is available
echo -e "\nChecking openspace CLI..."
if command -v openspace &> /dev/null; then
    echo "✅ openspace CLI is available"
    openspace --help | head -5
else
    echo "❌ openspace CLI not found"
    exit 1
fi

# Test basic functionality
echo -e "\nTesting basic functionality..."
echo "Testing openspace-mcp help output..."
result=$(openspace-mcp --help 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✅ openspace-mcp responds correctly"
else
    echo "❌ openspace-mcp failed to respond"
    exit 1
fi

echo -e "\n🧪 OpenSpace verification completed successfully!"
echo "✅ All tools are properly installed and accessible"
