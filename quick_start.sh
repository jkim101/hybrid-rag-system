#!/bin/bash
# Quick Start Script for Hybrid RAG System

echo "🤖 HYBRID RAG SYSTEM - QUICK START 🤖"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "✓ Dependencies installed"

# Download spaCy model
echo "📥 Downloading spaCy model..."
python -m spacy download en_core_web_sm > /dev/null 2>&1
echo "✓ spaCy model downloaded"

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo ""
    echo "Please create a .env file with your Google API key:"
    echo "  1. Copy .env.example to .env"
    echo "  2. Add your API key: GOOGLE_API_KEY=your_key_here"
    echo "  3. Get API key from: https://makersuite.google.com/app/apikey"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✓ Environment configured"
echo ""
echo "======================================"
echo "🎉 Setup complete!"
echo "======================================"
echo ""
echo "Quick start commands:"
echo ""
echo "  1. Test the system:"
echo "     python test_system.py"
echo ""
echo "  2. Run examples:"
echo "     python examples.py"
echo ""
echo "  3. Ingest documents and start server:"
echo "     python main.py --ingest --server"
echo ""
echo "  4. Interactive queries:"
echo "     python main.py --query"
echo ""
echo "  5. API documentation (after starting server):"
echo "     http://localhost:8000/docs"
echo ""
echo "======================================"
echo "📚 For more information, see:"
echo "   - README.md"
echo "   - PROJECT_SUMMARY.md"
echo "======================================"
