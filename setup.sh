#!/bin/bash
# Setup script for Cloud Cost Optimizer

set -e  # Exit on error

echo "=========================================="
echo "Cloud Cost Optimizer - Setup Script"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    REQUIRED_VERSION="3.10"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${RED}✗ Python $REQUIRED_VERSION or higher required, found $PYTHON_VERSION${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.10 or higher${NC}"
    exit 1
fi

echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}! Virtual environment already exists${NC}"
fi

echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

echo ""

# Install dependencies
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""

# Create necessary directories
echo "Creating project directories..."
mkdir -p data
mkdir -p models
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"

echo ""

# Copy environment file
echo "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}! Please edit .env file with your configuration${NC}"
else
    echo -e "${YELLOW}! .env file already exists, skipping${NC}"
fi

echo ""

# Create .gitignore
echo "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Project specific
data/
models/
logs/
*.db
*.log

# Environment
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Distribution
dist/
build/
*.egg-info/
EOF
echo -e "${GREEN}✓ .gitignore created${NC}"

echo ""

# Run tests
echo "Running tests..."
if python -m pytest test_optimizer.py -v --tb=short; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${YELLOW}! Some tests failed, but installation is complete${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Quick Start Commands:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the demo:"
echo "   python demo.py"
echo ""
echo "3. Start the API server:"
echo "   python main.py"
echo "   # API at http://localhost:8000"
echo ""
echo "4. Start the web interface:"
echo "   streamlit run streamlit_app.py"
echo "   # UI at http://localhost:8501"
echo ""
echo "5. Run tests:"
echo "   pytest test_optimizer.py -v"
echo ""
echo -e "${YELLOW}Note: First LLM run will download ~14GB model${NC}"
echo -e "${YELLOW}Set USE_LLM=false in .env to disable LLM${NC}"
echo ""
echo "Documentation: See README.md for full details"
echo ""