---
name: [Feature Name]
description: [One-line summary of what this feature does]
targets:
  - src/[module]/[file].py
  - src/[module]/[other].py
---

<!--
  This is a tesslio-style living spec (.spec.md). Copy it to your project's specs/
  directory, rename to <feature>.spec.md, and replace the placeholders.

  Rules:
  - `targets` lists ≥1 relative path or glob the spec covers (relative to THIS file).
  - Put `[@test]` links INLINE, right next to the requirement they verify — never grouped at the end.
  - Add prose context around each requirement so a reader knows what is being checked.
  - One spec per logical feature. Keep it scannable and synchronized with the code.
  - Validate with: scripts/validate-specs.sh (structure) and scripts/check-spec-links.sh (links resolve).
-->

# [Feature Name]

## [Functional area, e.g. Core behavior]

[Describe the expected behavior in prose, then link the test that verifies it.]

- [Requirement: what MUST happen]
  `[@test] tests/[area]/test_[behavior].py`
- [Edge case / error condition: what happens and how it's signaled]
  `[@test] tests/[area]/test_[edge_case].py`

### API contract *(optional)*
```python
def example(arg: str) -> Result: ...   # signature(s) the implementation must expose
```

## [Second functional area]

- [Requirement]
  `[@test] tests/[area]/test_[other].py`
