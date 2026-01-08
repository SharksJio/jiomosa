# Quick Release Commands

## When You Want to Create a Release

Just say any of these to me:

### 🎯 Simple Commands
- "Create a release version"
- "Make a new release"
- "I want to release a new version"
- "Prepare a release build"

### 🎯 Specific Version Type
- "Create a **PATCH** release" (bug fixes)
- "Create a **MINOR** release" (new features)
- "Create a **MAJOR** release" (breaking changes)

### 🎯 With Details
- "Create a release to fix the login bug" → PATCH
- "Release new version with Teams integration" → MINOR
- "Create release v1.1.0" → Specific version

## What I Will Do

When you ask for a release, I will:

1. ✅ **Ask for confirmation** on version type if not specified
2. ✅ **Run security checks**:
   - Scan for hardcoded secrets
   - Check debug logging
   - Review permissions
   - Validate ProGuard rules
3. ✅ **Review code quality**
4. ✅ **Increment version** (automatically)
5. ✅ **Update documentation** (VERSION.md)
6. ✅ **Build release APK**
7. ✅ **Run tests** if available
8. ✅ **Provide signing instructions**

## Or Run It Yourself

```bash
./make-release.sh
```

The script will guide you through the process interactively.

## Current Version

**1.0.0** (build 1) - Initial Release

## Version History

See [VERSION.md](VERSION.md) for complete changelog.

## Need Help?

- **Full process**: See [VERSIONING.md](VERSIONING.md)
- **Setup info**: See [VERSIONING_SETUP.md](VERSIONING_SETUP.md)
- **Changelog**: See [VERSION.md](VERSION.md)
