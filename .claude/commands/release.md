---
description: Run CI, bump version, commit and tag a new release
---

You are helping create a new release. Follow these steps:

1. **Run CI checks**: Execute `make ci` to run all CI checks (formatting, linting, type-checking, and tests)

2. **If CI fails**: Stop and report the failures to the user. Do not proceed with the release.

3. **If CI passes**: Ask the user what type of version bump they want:
   - **patch**: Bug fixes and minor changes (0.5.2 -> 0.5.3)
   - **minor**: New features, backward compatible (0.5.2 -> 0.6.0)
   - **major**: Breaking changes (0.5.2 -> 1.0.0)

4. **Read current version**: Read the version from `pyproject.toml`

5. **Calculate and update version**:
   - Parse the current version (format: MAJOR.MINOR.PATCH)
   - Increment the appropriate part based on user's choice
   - Update the version in BOTH `pyproject.toml` AND `src/token_bowl_chat/__init__.py`
   - CRITICAL: Both files must have the exact same version or tests will fail

6. **Commit changes**: Create a commit with the message: `Bump version to X.Y.Z`

7. **Create git tag**: Tag the commit with `vX.Y.Z` (e.g., `v0.5.3`)

8. **Remind user**: Let them know they can push the changes and tag with:
   ```bash
   git push && git push --tags
   ```

Remember:
- Only bump the version if CI passes completely
- Use semantic versioning (MAJOR.MINOR.PATCH)
- The user (rspectre) must push changes manually per project instructions
