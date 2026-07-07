# Contributing to useful-scripts

Welcome! 🎉 We're excited you're here. This repo exists because people like you take two minutes to share a script that saves someone ten.

---

## How to Contribute a Script

1. **Fork** this repository.
2. **Create a branch**: `git checkout -b add/my-script-name`
3. **Add your script** in the right language folder (e.g. `python/`, `javascript/`, `bash/`).
   - If your script needs its own assets (config files, images, etc.), give it **its own subdirectory** (e.g. `python/my-script/`).
   - If it's a single file, it can live directly in the language folder.
4. **Add a comment header** at the top of your script:
   ```javascript
   // -------------------------------------------------
   // Script Name:   My Script
   // Language:      JavaScript
   // Description:   What does this do in one line?
   // Usage:         node my-script.js <arg1> <arg2>
   // Author:        Your Name (optional)
   // -------------------------------------------------
   ```
5. **Update the README table** — add your script to the "Script Directory" table in [`README.md`](README.md) with its name, language, description, and a one-liner usage example.
6. **Commit**: `git commit -m "Add my-script-name"`
7. **Push**: `git push origin add/my-script-name`
8. **Open a Pull Request** on GitHub.

---

## Requirements

| Requirement | Why it matters |
|-------------|----------------|
| **Plug-and-play** | User should only need to run the file — no pip installs, npm init, or manual config beyond what's in the script header. |
| **Self-documenting** | Include a comment header (see template above) and inline comments for non-obvious steps. |
| **Safe defaults** | If your script modifies data, include a dry-run mode or a confirmation prompt as the default. |
| **Cross-platform** | Prefer Python 3, Node.js, or Bash. If your script is platform-specific, note it in the header. |
| **No secrets** | Never commit API keys, tokens, or passwords. Use environment variables or a `.env.example` file. |

---

## Code Style

- **Keep it short.** A script should fit in a single file unless assets are required.
- **Use comments** to explain *why*, not *what*.
- **Fail gracefully.** Wrap risky operations in try/catch and print helpful error messages.
- **Language conventions** — follow typical style for the language (e.g. snake_case for Python, camelCase for JS).

---

## Not sure what to build?

Check the [Issues](https://github.com/<your-org>/useful-scripts/issues) tab — look for the `script-idea` label. Pick one up and leave a comment so nobody duplicates your work.

---

## Questions?

Open a [Discussion](https://github.com/<your-org>/useful-scripts/discussions) or tag `@maintainers` on your PR. We're friendly, we promise.
