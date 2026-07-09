"""Build pipeline: validate -> backup -> write -> build -> test -> push"""
import os
import shutil
import subprocess
import tempfile
import time
from config import SITE_ROOT, SITE_DIR

# Lock file for preventing concurrent edits
LOCK_FILE = os.path.join(SITE_ROOT, "admin_cms", ".edit_lock")


def _lock_exclusive(fd):
    """Take a non-blocking exclusive lock. Raises OSError if already held."""
    try:
        import fcntl
    except ImportError:
        import msvcrt
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(fd):
    try:
        import fcntl
    except ImportError:
        import msvcrt
        fd.seek(0)
        msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


class PipelineError(Exception):
    def __init__(self, step, message, auto_restored=False):
        self.step = step
        self.message = message
        self.auto_restored = auto_restored
        super().__init__(f"[{step}] {message}")


class EditLock:
    """File-based exclusive lock for edit operations."""
    def __init__(self):
        self._fd = None

    def acquire(self, timeout=30):
        self._fd = open(LOCK_FILE, 'w')
        start = time.time()
        while True:
            try:
                # OSError covers both flock's BlockingIOError and the plain
                # OSError msvcrt.locking raises when the region is held.
                _lock_exclusive(self._fd)
                self._fd.write(str(os.getpid()))
                self._fd.flush()
                return True
            except OSError:
                if time.time() - start > timeout:
                    self._fd.close()
                    self._fd = None
                    return False
                time.sleep(0.5)

    def release(self):
        if self._fd:
            try:
                _unlock(self._fd)
                self._fd.close()
            except Exception:
                pass
            self._fd = None

    def __enter__(self):
        if not self.acquire():
            raise PipelineError("lock", "Another edit is in progress. Please try again.")
        return self

    def __exit__(self, *args):
        self.release()


def jekyll_build() -> tuple:
    """Run Jekyll build. Returns (success, output).

    Resolves `bundle` against known install paths so the admin server
    works regardless of how its PATH was set up at startup. Falls back
    to plain `bundle` (relying on $PATH) if none of the known paths
    exist, which keeps things working on dev machines with a normal
    Ruby install.
    """
    bundle_cmd = None
    for candidate in (
        "/home/i0179/miniconda3/envs/RS/bin/bundle",
        "/usr/local/bin/bundle",
        "/usr/bin/bundle",
    ):
        if os.path.exists(candidate):
            bundle_cmd = candidate
            break
    # Nothing at the known POSIX paths (dev boxes, Windows): fall back to PATH,
    # which also resolves bundle.bat from a RubyInstaller install.
    bundle_cmd = bundle_cmd or shutil.which("bundle") or "bundle"

    # bundle needs Ruby's gem env to find jekyll's executable. The
    # conda RS env keeps those gems under share/rubygems/{bin,gems};
    # without GEM_HOME and the gem bin on PATH, `bundle exec jekyll`
    # bails with "command not found: jekyll".
    env = os.environ.copy()
    if bundle_cmd.startswith("/home/i0179/miniconda3/envs/RS/"):
        gem_home = "/home/i0179/miniconda3/envs/RS/share/rubygems"
        env["GEM_HOME"] = gem_home
        env["PATH"] = (
            f"{gem_home}/bin:/home/i0179/miniconda3/envs/RS/bin:"
            + env.get("PATH", "")
        )

    try:
        result = subprocess.run(
            [bundle_cmd, "exec", "jekyll", "build"],
            cwd=SITE_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Jekyll build timed out (120s)"
    except Exception as e:
        return False, str(e)


def smoke_test() -> tuple:
    """Check that essential pages exist after build. Returns (success, details)."""
    essential_pages = [
        "index.html",
        "students.html",
        "news.html",
        "faculty.html",
        "alumni.html",
        "international.html",
    ]

    missing = []
    for page in essential_pages:
        path = os.path.join(SITE_DIR, page)
        if not os.path.exists(path):
            missing.append(page)
        elif os.path.getsize(path) < 500:
            missing.append(f"{page} (too small)")

    if missing:
        return False, f"Missing/broken pages: {', '.join(missing)}"
    return True, "All essential pages OK"


def git_commit(message: str, files: list) -> tuple:
    """Stage specific files and commit (no push). Returns (success, output)."""
    try:
        for f in files:
            subprocess.run(["git", "add", f], cwd=SITE_ROOT, capture_output=True, timeout=10)

        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=SITE_ROOT, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            if "nothing to commit" in result.stdout + result.stderr:
                return True, "No changes to commit"
            return False, result.stdout + result.stderr

        return True, "Committed locally"
    except subprocess.TimeoutExpired:
        return False, "Git operation timed out"
    except Exception as e:
        return False, str(e)


def _get_pending_site_files() -> list:
    """Get list of uncommitted files that affect the public site (templates, data, assets, includes).
    Excludes admin_cms internals, ai_server runtime files, logs, etc.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=SITE_ROOT, capture_output=True, text=True, timeout=10
        )
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # Format: "XY filename" where X,Y are status chars
            status = line[:2]
            path = line[3:].strip()
            # Handle renamed files "XY old -> new"
            if ' -> ' in path:
                path = path.split(' -> ')[-1]
            # Strip quotes
            if path.startswith('"') and path.endswith('"'):
                path = path[1:-1]

            # Only include site-affecting files
            site_prefixes = (
                '_data/', '_includes/', '_layouts/', '_portfolio/',
                'assets/', 'img/', '_config.yml',
                # Korean folder referenced by sitetext.yml slider entries.
                # Without this prefix the CMS auto-commit missed newly uploaded
                # slider images (e.g. img_2934.jpg → site 404 while local dev
                # served the on-disk file).
                '참고 이미지/',
            )
            site_extensions = (
                '.md', '.html', '.yml', '.yaml',
                # Image formats accepted by image_manager.save_image —
                # required so uploads under arbitrary site folders also get
                # auto-staged for push.
                '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
            )

            is_site_file = (
                path.startswith(site_prefixes) or
                (not path.startswith(('admin_cms/', 'ai_server/', '.claude/',
                                      'finetune_env/', '_site/'))
                 and any(path.endswith(ext) for ext in site_extensions))
            )
            # Explicitly exclude admin internals and runtime files
            is_excluded = path.startswith((
                'admin_cms/', 'ai_server/', '.claude/', 'finetune_env/',
                '_site/', '.gitignore'
            )) or path.endswith(('.log', '.pid', '.lock', '.tmp'))

            if is_site_file and not is_excluded:
                files.append(path)
        return files
    except Exception:
        return []


def git_push() -> tuple:
    """Push all local commits to remote. Auto-commits any pending site files first.
    Returns (success, output).
    """
    try:
        # Auto-commit any pending site files (templates, data, assets) before push
        pending = _get_pending_site_files()
        if pending:
            for f in pending:
                subprocess.run(["git", "add", f], cwd=SITE_ROOT,
                               capture_output=True, timeout=10)
            commit_result = subprocess.run(
                ["git", "commit", "-m", f"CMS: Auto-commit pending site changes ({len(pending)} files)"],
                cwd=SITE_ROOT, capture_output=True, text=True, timeout=30
            )
            # OK if "nothing to commit" - some files may already be staged elsewhere
            if commit_result.returncode != 0 and "nothing to commit" not in commit_result.stdout + commit_result.stderr:
                pass  # continue to push anyway

        result = subprocess.run(
            ["git", "push"], cwd=SITE_ROOT, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return False, f"Push failed: {result.stderr}"

        msg = "Pushed to remote successfully"
        if pending:
            msg += f" (auto-committed {len(pending)} pending file(s))"
        return True, msg
    except subprocess.TimeoutExpired:
        return False, "Push timed out"
    except Exception as e:
        return False, str(e)


def has_unpushed_commits() -> dict:
    """Check if there are local commits not pushed to remote."""
    try:
        result = subprocess.run(
            ["git", "log", "origin/main..HEAD", "--oneline"],
            cwd=SITE_ROOT, capture_output=True, text=True, timeout=10
        )
        lines = [l for l in result.stdout.strip().split('\n') if l]
        return {"unpushed": len(lines), "commits": lines}
    except Exception:
        return {"unpushed": 0, "commits": []}


def full_deploy(yaml_filename: str, data: dict, operation: str,
                validate_fn=None, extra_files=None):
    """Full deploy pipeline with safety.

    Args:
        yaml_filename: key from EDITABLE_FILES (e.g., 'members')
        data: the complete YAML data to write
        operation: description for backup/commit
        validate_fn: optional validation function(data) -> list of errors
        extra_files: additional files to stage (e.g., uploaded images)

    Returns:
        dict with status, backup_id, message
    """
    from backup_manager import create_backup, restore_backup
    from yaml_manager import write_yaml, get_yaml_path
    from config import EDITABLE_FILES

    # Step 1: Validate
    if validate_fn:
        errors = validate_fn(data)
        if errors:
            return {"status": "error", "step": "validate", "errors": errors}

    backup_id = None
    yml_name = EDITABLE_FILES[yaml_filename]
    yml_rel_path = os.path.join("_data", yml_name)
    files_to_stage = [yml_rel_path]
    if extra_files:
        files_to_stage.extend(extra_files)

    with EditLock():
        # Step 2: Backup
        backup_id = create_backup(operation, [yaml_filename])

        # Step 3: Write YAML
        try:
            write_yaml(yaml_filename, data)
        except Exception as e:
            restore_backup(backup_id)
            return {"status": "error", "step": "write", "message": str(e),
                    "auto_restored": True, "backup_id": backup_id}

        # Step 4: Jekyll build
        success, output = jekyll_build()
        if not success:
            restore_backup(backup_id)
            # Rebuild with restored data
            jekyll_build()
            return {"status": "error", "step": "build", "message": output,
                    "auto_restored": True, "backup_id": backup_id}

        # Step 5: Smoke test
        success, details = smoke_test()
        if not success:
            restore_backup(backup_id)
            jekyll_build()
            return {"status": "error", "step": "smoke_test", "message": details,
                    "auto_restored": True, "backup_id": backup_id}

        # Step 6: Git commit (no push - user pushes manually via "Apply" button)
        commit_msg = f"CMS: {operation}"
        success, git_output = git_commit(commit_msg, files_to_stage)

        # Step 7: If chatbot knowledge changed, rebuild RAG so chatbot uses new info immediately
        rag_status = ""
        if yaml_filename == "chatbot_knowledge":
            rag_success, rag_output = trigger_rag_update()
            if rag_success:
                rag_status = " RAG updated."
            else:
                rag_status = f" RAG update failed: {rag_output[:80]}"

        return {
            "status": "success",
            "backup_id": backup_id,
            "message": f"Saved. {git_output}{rag_status}",
            "pushed": False,
        }


def trigger_rag_update() -> tuple:
    """Trigger update_rag.sh in BACKGROUND so the user doesn't wait for RAG rebuild.
    RAG rebuild takes ~1-2 minutes (sentence-transformer load + FAISS index build + chatbot restart).
    Returns (success, output) immediately after spawning the background job.
    """
    try:
        rag_script = os.path.join(SITE_ROOT, "ai_server", "update_rag.sh")
        if not os.path.exists(rag_script):
            return False, "update_rag.sh not found"

        # The script is bash; on Windows it runs under Git for Windows' bash.
        bash = "/bin/bash" if os.path.exists("/bin/bash") else shutil.which("bash")
        if not bash:
            return False, "bash not found — cannot run update_rag.sh"

        log_file = os.path.join(tempfile.gettempdir(), "admin_rag_update.log")
        # start_new_session is POSIX-only; DETACHED_PROCESS is its Windows analogue.
        detach = ({"start_new_session": True} if os.name == "posix"
                  else {"creationflags": getattr(subprocess, "DETACHED_PROCESS", 0)})
        subprocess.Popen(
            [bash, rag_script],
            cwd=SITE_ROOT,
            stdout=open(log_file, "a"),
            stderr=subprocess.STDOUT,
            **detach,
        )
        return True, "RAG rebuild started in background (~1-2min until chatbot picks up)"
    except Exception as e:
        return False, str(e)
