#!/bin/bash

# Configuration
PYTHON_BIN="./venv/bin/python3"
SCRIPT_PY="./firmware_sign_tool.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ "$#" -ne 2 ]; then
    echo -e "${RED}Usage: $0 <input_file.hex|.bin> <private_key.pem>${NC}"
    exit 1
fi

INPUT_PATH="$1"
PRIVATE_KEY="$2"
DATE=$(date +%Y%m%d)
OUTPUT_SIGNED="app_sign_${DATE}.bin"

echo -e "${BLUE}GachBoot Firmware Signing Workflow${NC}"

# 1. Check for Virtual Environment
if [ ! -f "$PYTHON_BIN" ]; then
    echo -e "${RED}Error: Virtual environment not found at ./venv${NC}"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install cryptography"
    exit 1
fi

# 2. Check if input file exists
if [ ! -f "$INPUT_PATH" ]; then
    echo -e "${RED}Error: Input file '$INPUT_PATH' not found.${NC}"
    exit 1
fi

# 3. Check for Private Key
if [ ! -f "$PRIVATE_KEY" ]; then
    echo -e "${RED}Error: Private key '$PRIVATE_KEY' not found.${NC}"
    exit 1
fi

# 4. Handle HEX to BIN conversion if necessary
WORKING_BIN="$INPUT_PATH"
if [[ "$INPUT_PATH" == *.hex ]]; then
    WORKING_BIN="${INPUT_PATH%.hex}.bin"
    echo -e "${BLUE}Converting $INPUT_PATH to $WORKING_BIN...${NC}"
    objcopy -I ihex -O binary "$INPUT_PATH" "$WORKING_BIN"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to convert HEX to BIN.${NC}"
        exit 1
    fi
fi

# 5. Sign the Binary
echo -e "${BLUE}Signing $WORKING_BIN...${NC}"
$PYTHON_BIN "$SCRIPT_PY" \
    --input "$WORKING_BIN" \
    --private-key "$PRIVATE_KEY" \
    --output "$OUTPUT_SIGNED" \
    --verbose

if [ $? -eq 0 ]; then
    echo -e "${GREEN}------------------------------------------------${NC}"
    echo -e "${GREEN}Success! Signed package created: $OUTPUT_SIGNED${NC}"
    echo -e "${GREEN}------------------------------------------------${NC}"
    
    # Verify the package
    echo -e "${BLUE}Verifying package...${NC}"
    $PYTHON_BIN "$SCRIPT_PY" --inspect "$OUTPUT_SIGNED"

    # 6. Cleanup temporary bin if it was converted from hex
    if [[ "$INPUT_PATH" == *.hex ]] && [ -f "$WORKING_BIN" ]; then
        echo -e "${BLUE}Cleaning up temporary file $WORKING_BIN...${NC}"
        rm "$WORKING_BIN"
    fi
else
    echo -e "${RED}Error: Signing failed.${NC}"
    exit 1
fi
