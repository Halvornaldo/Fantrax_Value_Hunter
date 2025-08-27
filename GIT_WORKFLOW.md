# Git Workflow Best Practices
## Fantrax Value Hunter Development

### **Branch Strategy**

**Main Branches:**
- `master` - Production-ready code
- `feature/*` - Feature development branches
- `hotfix/*` - Emergency fixes for production

**Current Setup:**
- Working on: `feature/gameweek-unification`
- Next: Create focused feature branches for new work

### **Commit Message Standards**

**Format:**
```
<type>: <short description>

<optional longer description>

<breaking changes or special notes>

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `style`: Code formatting changes
- `refactor`: Code restructuring without behavior changes
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

### **Development Workflow**

1. **Start New Feature:**
   ```bash
   git checkout master
   git pull origin master
   git checkout -b feature/feature-name
   ```

2. **Regular Development:**
   ```bash
   git add <specific-files>
   git commit -m "feat: descriptive commit message"
   git push origin feature/feature-name
   ```

3. **Feature Complete:**
   ```bash
   git push origin feature/feature-name
   # Create pull request on GitHub
   # After review, merge to master
   git checkout master
   git pull origin master
   git branch -d feature/feature-name
   ```

### **Current Project Status**

**Recently Completed (2025-08-27):**
- ✅ Fixed critical blending parameter configuration 
- ✅ Enhanced CSV export with Understat data
- ✅ Added React dashboard with Dynamic PPG
- ✅ Updated comprehensive V2.0 documentation
- ✅ Organized git history with proper commits

**Active Branch:** `feature/gameweek-unification`
- 6 organized commits following best practices
- Ready for merge to master once tested
- Pull request available at: https://github.com/Halvornaldo/Fantrax_Value_Hunter/pull/new/feature/gameweek-unification

### **Best Practices Applied**

1. **Atomic Commits:** Each commit addresses one logical change
2. **Meaningful Messages:** Clear descriptions of what and why
3. **Organized History:** Logical sequence of changes
4. **Clean .gitignore:** Proper exclusion of build artifacts and sensitive data
5. **Branch Naming:** Descriptive feature branch names
6. **Documentation:** Changes documented alongside code

### **Next Steps Workflow**

1. **Create Pull Request:**
   - Review changes in GitHub
   - Add detailed PR description
   - Request review if working with team

2. **New Features:**
   ```bash
   # Always branch from master for new features
   git checkout master
   git pull origin master
   git checkout -b feature/new-feature-name
   ```

3. **Regular Maintenance:**
   ```bash
   # Keep feature branch up to date
   git checkout feature/current-feature
   git merge master
   # Or use rebase for cleaner history
   git rebase master
   ```

### **Emergency Hotfix Process**

```bash
git checkout master
git pull origin master
git checkout -b hotfix/critical-fix
# Make fixes
git add .
git commit -m "hotfix: fix critical production issue"
git push origin hotfix/critical-fix
# Create PR and merge immediately
```

### **Code Quality Checks**

Before each commit:
1. ✅ Test functionality works
2. ✅ Run linting/formatting (if configured)
3. ✅ Update documentation if needed
4. ✅ Check no sensitive data in commit
5. ✅ Meaningful commit message

### **Remote Repository Management**

**Current Setup:**
- Origin: https://github.com/Halvornaldo/Fantrax_Value_Hunter.git
- Default branch: master
- Feature branch pushed: feature/gameweek-unification

**Commands Reference:**
```bash
# View remote info
git remote -v

# Check status
git status

# View recent commits
git log --oneline -10

# View all branches
git branch -a

# Clean up merged branches
git branch -d feature/completed-feature
git push origin --delete feature/completed-feature
```

---

**Setup Complete:** ✅ Git workflow now follows industry best practices with organized history, proper branching, and meaningful commit messages.