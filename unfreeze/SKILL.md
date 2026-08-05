---
name: unfreeze
description: |
  Clear the directory-edit boundary set by /freeze, allowing edits everywhere again.
  Use this skill whenever the user says "unfreeze", "unlock edits", "remove freeze",
  "allow all edits", "lift the restriction", or otherwise wants to widen edit scope
  without ending the session. Also triggers on /unfreeze.
---

# Unfreeze — Remove the Edit Boundary

Clear the freeze boundary set by `/freeze`, so Edit and Write can target any file
again for the rest of the session.

## What to do

1. Look for the freeze-state file (default: `.freeze-dir` in cwd, or `~/.cache/freeze`).
2. If it exists, read the previous boundary, then delete the file.
3. Report the result to the user:

   - If a boundary was active:
     > "Freeze boundary cleared (was: `<path>/`). Edits are now allowed everywhere."
   - If no boundary was set:
     > "No freeze boundary was active."

4. Note that to re-freeze with a different directory, the user can run `/freeze`
   again.

## Why this exists

Sometimes you start narrow ("only touch the auth module") and then realize a fix
actually needs a touch in a shared util. Rather than ending the session or working
around the freeze with `sed -i`, lift the boundary explicitly. That keeps the
decision visible in the conversation history.
