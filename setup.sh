#!/bin/bash

# Hybrid RAG System - Setup Script
# This script automates the installation and setup process

set -e  # Exit on error

echo "================================================"
echo "Hybrid RAG System - Installation Script"
echo "================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "Python $PYTHON_VERSION found"
else
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Are you in the project root directory?"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --break-system-packages 2>/dev/null || pip install --upgrade pip
print_status "Pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt
print_status "Dependencies installed"

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p chroma_db
mkdir -p data/documents
mkdir -p data/evaluation
mkdir -p temp_uploads
mkdir -p temp_eval
print_status "Directories created"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status ".env file created from template"
        print_warning "Please edit .env file and add your GEMINI_API_KEY"
    else
        echo "GEMINI_API_KEY=your_api_key_here" > .env
        print_status ".env file created"
        print_warning "Please edit .env file and add your GEMINI_API_KEY"
    fi
else
    print_warning ".env file already exists"
fi

# Installation complete
echo ""
echo "================================================"
print_status "Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env file and add your Gemini API key:"
echo "     ${YELLOW}nano .env${NC}"
echo ""
echo "  2. Run the main application:"
echo "     ${GREEN}streamlit run ui/streamlit_app.py${NC}"
echo ""
echo "  3. Or run the evaluation interface:"
echo "     ${GREEN}streamlit run ui/evaluation_ui.py${NC}"
echo ""
echo "  4. To deactivate virtual environment:"
echo "     ${YELLOW}deactivate${NC}"
echo ""
echo "For more information, see README.md"
echo ""
