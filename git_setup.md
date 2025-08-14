# Git Setup Guide - Fantrax Value Hunter

## 🚀 **Initial Repository Setup**

### **1. Initialize Git Repository**
```bash
# Navigate to project directory
cd Fantrax_Value_Hunter

# Initialize git repository
git init

# Add all files (respecting .gitignore)
git add .

# Initial commit
git commit -m "Initial commit: Phase 1 foundation complete

✅ Complete API access and authentication system
✅ Form tracking with weighted recent games  
✅ 2024-25 baseline data preservation
✅ Comprehensive documentation suite
✅ Dashboard specification ready for Phase 3

- API access to all 633 players across 32 pages
- Form calculation framework with 3/5-game lookback
- Complete dashboard implementation guide
- Project structure with proper .gitignore"
```

### **2. Create GitHub Repository (Optional)**
```bash
# Create GitHub repository (if using GitHub)
gh repo create fantrax-value-hunter --public --description "Fantasy Football Analytics Platform for Fantrax leagues"

# Add remote origin
git remote add origin https://github.com/yourusername/fantrax-value-hunter.git

# Push to GitHub
git push -u origin main
```

---

## 📋 **Git Workflow & Best Practices**

### **Branch Strategy**
```bash
# Main branches
main              # Production-ready code
develop           # Integration branch for features

# Feature branches
feature/phase2-fixture-difficulty    # OddsChecker integration
feature/phase2-starter-prediction    # Fantasy Football Scout scraping
feature/phase3-dashboard             # Flask web interface
feature/phase3-drag-drop            # Lineup builder
```

### **Commit Message Convention**
```bash
# Format: <type>(<scope>): <description>
# 
# Types: feat, fix, docs, style, refactor, test, chore
# Scope: form-tracker, dashboard, api, docs, config

# Examples:
git commit -m "feat(form-tracker): add weighted 5-game lookback option"
git commit -m "docs(dashboard): complete three-panel layout specification"
git commit -m "fix(api): handle pagination timeout errors"
git commit -m "test(form-tracker): add unit tests for season switching"
git commit -m "chore(config): update requirements.txt with Flask dependencies"
```

### **Feature Development Workflow**
```bash
# 1. Create feature branch
git checkout -b feature/phase2-fixture-difficulty

# 2. Make changes and commit regularly
git add src/fixture_scraper.py
git commit -m "feat(fixture): add OddsChecker scraping foundation"

git add tests/test_fixture_scraper.py  
git commit -m "test(fixture): add unit tests for odds parsing"

# 3. Push feature branch
git push -u origin feature/phase2-fixture-difficulty

# 4. Create pull request (GitHub) or merge to develop
git checkout develop
git merge feature/phase2-fixture-difficulty

# 5. Clean up
git branch -d feature/phase2-fixture-difficulty
```

---

## 🔒 **Security & Sensitive Data**

### **Protected Files (.gitignore)**
```bash
# These files are automatically ignored:
config/fantrax_cookies.json    # Authentication cookies
data/                          # Cached player data  
*.env                         # Environment variables
*.log                         # Log files
__pycache__/                  # Python cache
```

### **Configuration Management**
```bash
# Use example files for sensitive config
cp config/fantrax_cookies.json.example config/fantrax_cookies.json

# Never commit actual authentication data
git status  # Should NOT show fantrax_cookies.json
```

---

## 📊 **Release Management**

### **Version Tagging**
```bash
# Phase releases
git tag -a v1.0.0 -m "Phase 1: Foundation complete - API access and form tracking"
git tag -a v2.0.0 -m "Phase 2: Enhanced analytics with fixture difficulty"  
git tag -a v3.0.0 -m "Phase 3: Dashboard with real-time parameter controls"

# Push tags
git push origin --tags
```

### **Release Notes Format**
```markdown
# Release v2.0.0 - Enhanced Analytics

## 🚀 New Features
- Fixture difficulty integration from OddsChecker.com
- Predicted starter data from Fantasy Football Scout
- Mathematical formula validation system

## 🐛 Bug Fixes  
- Fixed form calculation edge cases for new players
- Improved API pagination error handling

## 📋 Documentation
- Updated dashboard specification with boost factors
- Added testing guidelines and examples

## ⚠️ Breaking Changes
- config/system_parameters.json structure updated
- Form tracking API changed (see migration guide)
```

---

## 🧪 **Testing Integration**

### **Pre-commit Hooks**
```bash
# Install pre-commit (optional but recommended)
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
-   repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
    -   id: black
-   repo: https://github.com/pycqa/flake8  
    rev: 6.1.0
    hooks:
    -   id: flake8
-   repo: local
    hooks:
    -   id: tests
        name: tests
        entry: pytest tests/
        language: system
        pass_filenames: false
        always_run: true
EOF

# Install hooks
pre-commit install
```

### **Automated Testing**
```bash
# Run all tests before committing
pytest tests/ -v

# Run specific test categories
pytest tests/test_form_tracker.py -v
pytest tests/test_candidate_analyzer.py -v

# Check code coverage
pytest --cov=src tests/
```

---

## 🎯 **Next Steps After Git Setup**

1. **Initialize Repository**: Run git init and initial commit
2. **Set up GitHub** (optional): Create remote repository 
3. **Install Pre-commit Hooks**: Ensure code quality
4. **Create Feature Branch**: Start Phase 2 development
5. **Regular Commits**: Follow commit message convention

### **Ready to Start Development!** 🚀

The project is now properly structured with Git best practices. All sensitive data is protected, documentation is complete, and the foundation is ready for Phase 2 and Phase 3 development.