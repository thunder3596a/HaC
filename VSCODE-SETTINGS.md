# VSCode Settings Management

## Why VSCode Settings Are NOT in the Repository

VSCode settings (`.vscode/` folder and `*.code-workspace` files) are excluded from version control for several important reasons:

### Security Concerns
- **API Tokens:** Extensions like Gitea/Forgejo often store authentication tokens in `settings.json`
- **Local Paths:** Workspace settings contain absolute paths specific to your machine
- **Personal Info:** User-specific preferences that shouldn't be shared

### Portability Issues
- Settings are machine-specific and won't work on other systems
- Different team members may use different editors or extensions
- Local paths would break on other machines

## Recommended: Use VSCode Settings Sync

VSCode has built-in **Settings Sync** that backs up your settings to the cloud securely.

### What Gets Synced
- ✅ User settings
- ✅ Extensions
- ✅ Keyboard shortcuts
- ✅ UI state
- ✅ Snippets
- ✅ Profiles (for different workflows)

### What Doesn't Get Synced
- ❌ Workspace-specific settings (good - these are local)
- ❌ Sensitive tokens (stored separately in system keychain)

### How to Enable Settings Sync

1. **Open VSCode**
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
3. Type: `Settings Sync: Turn On`
4. Choose what to sync (recommended: select all)
5. Sign in with:
   - **GitHub** (recommended for developers)
   - **Microsoft Account**

### Benefits Over Git-Based Settings

| Feature | Settings Sync | Git Repository |
|---------|--------------|----------------|
| **Automatic backup** | ✅ Every change | ❌ Manual commits |
| **Cross-machine** | ✅ Instant sync | ⚠️ Requires pull |
| **Secure tokens** | ✅ Keychain | ❌ Exposed in repo |
| **Per-workspace** | ✅ Separate | ⚠️ Mixed with global |
| **Extension mgmt** | ✅ Auto-install | ❌ Manual |

## Alternative: Private Settings Repository

If you prefer full control, create a **private** dotfiles repository:

```bash
# Create private repo for your dotfiles
mkdir ~/dotfiles
cd ~/dotfiles
git init

# Copy VSCode settings
cp -r ~/.config/Code/User/* ./vscode/

# Symlink (Linux/Mac)
ln -s ~/dotfiles/vscode ~/.config/Code/User

# Or use junction (Windows)
mklink /J "%APPDATA%\Code\User" "C:\Users\YourName\dotfiles\vscode"
```

### ⚠️ CRITICAL: Add .gitignore

If using a dotfiles repo, **always exclude secrets**:

```gitignore
# .gitignore for dotfiles
*.token
*secrets.json
globalStorage/
workspaceStorage/
```

## For This Project

This repository uses `.gitignore` to exclude:
- `.vscode/` - All VSCode workspace settings
- `*.code-workspace` - Workspace definition files
- `.env*` - Environment files (except `.env.example`)

**Use Settings Sync** to backup your personal VSCode configuration instead.

## Workspace-Specific Settings (If Needed)

If you need to share workspace settings (e.g., recommended extensions for contributors):

### Create `.vscode/extensions.json` (Safe to Commit)

```json
{
  "recommendations": [
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml",
    "esbenp.prettier-vscode"
  ]
}
```

This suggests extensions without forcing configuration or exposing tokens.

### Create `.vscode/settings.json.example` (Template)

```json
{
  "gitea.instanceURL": "https://git.example.com",
  "gitea.owner": "your-username",
  "gitea.repo": "docker",
  "gitea.token": "REPLACE_WITH_YOUR_TOKEN"
}
```

Users can copy to `settings.json` and add their own token.

## Summary

✅ **DO:**
- Use VSCode Settings Sync for personal settings
- Create extension recommendations in `.vscode/extensions.json`
- Use `settings.json.example` as templates

❌ **DON'T:**
- Commit `.vscode/settings.json` with tokens
- Store workspace files in public repos
- Mix personal and project settings

---

**Related:**
- [VSCode Settings Sync Documentation](https://code.visualstudio.com/docs/editor/settings-sync)
- [Managing Extensions](https://code.visualstudio.com/docs/editor/extension-marketplace)
