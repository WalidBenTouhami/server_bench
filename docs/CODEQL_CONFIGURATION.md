# CodeQL Configuration Documentation

## Overview

This document explains the CodeQL workflow configuration for the server_bench project and addresses the "configuration not found" warning that can occur in pull requests.

## Configuration Format

The CodeQL workflow is configured in `.github/workflows/codeql.yml`. The key configuration element for ensuring proper configuration matching is the `category` parameter:

```yaml
- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v3
  with:
    category: "/language:${{ matrix.language }}"
```

For the complete workflow configuration, refer to `.github/workflows/codeql.yml` in the repository.

### Category Parameter

The `category` parameter is critical for configuration matching between branches. It must:
- Use consistent YAML formatting for the template variable: `${{ matrix.language }}`
- Follow the format: `/language:${{ matrix.language }}`
- Match exactly between main and PR branches

## Configuration Identifier

CodeQL generates a unique configuration identifier using:
- **File path**: `.github/workflows/codeql.yml`
- **Job name**: `analyze`
- **Category**: `/language:cpp` (after template expansion)

The full identifier becomes: `.github/workflows/codeql.yml:analyze/language:cpp`

## Common Issues

### "Configuration Not Found" Warning

**Symptom**: Pull requests show a warning that the configuration present on main was not found.

**Causes**:
1. The workflow hasn't completed a successful run on the PR branch yet
2. The category parameter format differs between branches
3. The workflow file path or job name has changed

**Resolution**:
1. Ensure the workflow file is identical between main and PR branches
2. Wait for the workflow to complete at least one successful run
3. Verify the category parameter uses consistent spacing

### Workflow Not Running

**Symptom**: Workflow shows 0 jobs with "action_required" status.

**Cause**: Workflow requires manual approval (common for bot-created PRs or first-time contributors)

**Resolution**: Request repository administrator to approve the workflow run

## Best Practices

1. **Consistent Formatting**: Maintain consistent YAML formatting for template variables
2. **No Modifications**: Keep the category format consistent across all branches
3. **Test Changes**: Ensure workflow completes successfully before merging

## References

- [GitHub CodeQL Documentation](https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors)
- [CodeQL Action Configuration](https://github.com/github/codeql-action)
