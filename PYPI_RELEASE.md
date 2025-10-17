# PyPI Release Guide

This guide explains how to build and publish Token Bowl Chat to PyPI. There are two methods:

1. **Automated (Recommended)**: GitHub Actions workflow automatically publishes on release
2. **Manual**: Build and publish locally using `uv`

## Method 1: Automated Publishing (Recommended)

### Setup (One-Time)

The repository includes a GitHub Actions workflow that automatically publishes to PyPI when you create a GitHub release.

#### Enable PyPI Trusted Publishing

1. **Go to PyPI**:
   - Visit https://pypi.org/manage/account/publishing/

2. **Add Trusted Publisher**:
   - Click "Add a new pending publisher"
   - Fill in the form:
     - **PyPI Project Name**: `token-bowl-chat`
     - **Owner**: `RobSpectre` (your GitHub username)
     - **Repository name**: `token-bowl-chat`
     - **Workflow name**: `publish.yml`
     - **Environment name**: `pypi`
   - Click "Add"

3. **Add TestPyPI Publisher** (optional but recommended):
   - Visit https://test.pypi.org/manage/account/publishing/
   - Add another publisher with the same details but environment name: `testpypi`

### Release Process

1. **Update version**:
   ```bash
   # Edit pyproject.toml and update version number
   version = "0.2.0"
   ```

2. **Update CHANGELOG.md** with release notes

3. **Commit changes**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.2.0"
   git push
   ```

4. **Create and push tag**:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

5. **Create GitHub Release**:
   - Go to https://github.com/RobSpectre/token-bowl-chat/releases/new
   - Select the tag you just created (v0.2.0)
   - Add release title: "v0.2.0"
   - Add release notes from CHANGELOG.md
   - Click "Publish release"

6. **Wait for workflow**:
   - GitHub Actions will automatically:
     - Build the package
     - Publish to TestPyPI
     - Publish to PyPI
   - Check progress at: https://github.com/RobSpectre/token-bowl-chat/actions

That's it! The package will be live on PyPI within minutes.

## Method 2: Manual Publishing

### Prerequisites

1. **Install uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Or on Windows:
   # powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Create PyPI account**:
   - Register at https://pypi.org/account/register/
   - Enable 2FA (required for uploading)
   - Create an API token at https://pypi.org/manage/account/token/

3. **Configure credentials**:

   Create or edit `~/.pypirc`:
   ```ini
   [pypi]
   username = __token__
   password = pypi-AgEIcHlwaS5vcmc...  # Your API token here
   ```

   Or use environment variable:
   ```bash
   export UV_PUBLISH_TOKEN=pypi-AgEIcHlwaS5vcmc...
   ```

### Pre-Release Checklist

Before building and uploading manually, ensure:

- [ ] All tests pass: `pytest`
- [ ] Code quality checks pass: `ruff check .`
- [ ] Type checking passes: `mypy src`
- [ ] Version number updated in `pyproject.toml`
- [ ] CHANGELOG.md updated with release notes
- [ ] README.md is up to date
- [ ] All changes committed to git
- [ ] Git tag created: `git tag v0.1.0`

### Building the Distribution

1. **Clean previous builds**:
   ```bash
   rm -rf dist/
   ```

2. **Build the package**:
   ```bash
   uv build
   ```

   This creates two files in the `dist/` directory:
   - `token_bowl_chat-0.1.0.tar.gz` (source distribution)
   - `token_bowl_chat-0.1.0-py3-none-any.whl` (wheel distribution)

3. **Verify the build**:
   ```bash
   # Check what files are included in source dist
   tar -tzf dist/token_bowl_chat-0.1.0.tar.gz

   # Check what files are in the wheel
   unzip -l dist/token_bowl_chat-0.1.0-py3-none-any.whl
   ```

### Testing the Package Locally

Before uploading to PyPI, test the package locally:

```bash
# Create a test environment with uv
uv venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from the wheel
uv pip install dist/token_bowl_chat-0.1.0-py3-none-any.whl

# Test import
python -c "from token_bowl_chat import TokenBowlClient; print('Success!')"

# Deactivate and remove test environment
deactivate
rm -rf test-env
```

### Uploading to Test PyPI (Recommended First)

Test PyPI is a separate instance of PyPI for testing:

1. **Register at Test PyPI**:
   - https://test.pypi.org/account/register/
   - Create a separate API token for Test PyPI

2. **Upload to Test PyPI**:
   ```bash
   uv publish --publish-url https://test.pypi.org/legacy/
   ```

   Or with explicit token:
   ```bash
   UV_PUBLISH_TOKEN=your-testpypi-token uv publish --publish-url https://test.pypi.org/legacy/
   ```

3. **Test installation from Test PyPI**:
   ```bash
   uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ token-bowl-chat
   ```

   Note: `--extra-index-url` is needed because dependencies come from regular PyPI.

### Uploading to PyPI (Production)

Once testing is complete:

1. **Upload the package**:
   ```bash
   uv publish
   ```

   Or with explicit token:
   ```bash
   UV_PUBLISH_TOKEN=your-pypi-token uv publish
   ```

2. **Verify upload**:
   - Check https://pypi.org/project/token-bowl-chat/

3. **Test installation**:
   ```bash
   uv pip install token-bowl-chat
   # Or with pip:
   pip install token-bowl-chat
   ```

## Post-Release Steps

1. **Push git tag**:
   ```bash
   git push origin v0.1.0
   ```

2. **Create GitHub release** (if using GitHub):
   - Go to repository releases page
   - Create a new release from the tag
   - Add release notes from CHANGELOG.md

3. **Announce the release**:
   - Update project documentation
   - Notify users/community

## Troubleshooting

### Package already exists
If you get "File already exists" error, you cannot overwrite a version. You must:
- Increment the version number in `pyproject.toml`
- Rebuild and reupload

### Missing files in distribution
Check `MANIFEST.in` or hatchling configuration in `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/token_bowl_chat"]
```

### Upload forbidden
- Ensure 2FA is enabled on your PyPI account
- Use an API token, not username/password
- Check token permissions (must have upload permission)
- Verify the token is set correctly (UV_PUBLISH_TOKEN or ~/.pypirc)

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes (e.g., 1.0.0 → 2.0.0)
- **MINOR** version: Backward-compatible new features (e.g., 1.0.0 → 1.1.0)
- **PATCH** version: Backward-compatible bug fixes (e.g., 1.0.0 → 1.0.1)

For pre-releases:
- Alpha: `0.1.0a1`
- Beta: `0.1.0b1`
- Release candidate: `0.1.0rc1`

## Quick Reference

```bash
# Full release workflow
pytest                          # Run tests
ruff check .                    # Lint
mypy src                        # Type check
rm -rf dist/                    # Clean
uv build                        # Build
uv publish                      # Upload to PyPI
```

**Or in one line:**
```bash
pytest && ruff check . && mypy src && rm -rf dist/ && uv build && uv publish
```

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)

## Why uv?

`uv` is a fast Python package installer and resolver written in Rust by Astral (the creators of Ruff). Benefits:

- **10-100x faster** than pip and pip-tools
- **Single tool** for building, publishing, and installing packages
- **Drop-in replacement** for pip, pip-tools, and build
- **Built-in virtual environment** management
- **Consistent and reliable** dependency resolution
