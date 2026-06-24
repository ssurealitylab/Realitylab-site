#!/usr/bin/env python3
"""
Reality Lab Admin CMS Server
Serves the actual Jekyll site with an editing overlay injected.
"""
import os
import sys
import json
import argparse
import mimetypes
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import (Flask, request, jsonify, session, send_from_directory,
                   send_file, redirect, render_template_string, Response)
from flask_cors import CORS

from config import (SITE_ROOT, SITE_DIR, DATA_DIR, CMS_PORT,
                    EDITABLE_FILES, MAX_UPLOAD_SIZE, IMAGE_DIRS,
                    LOGIN_LOCKOUT_MINUTES)
from auth import init_auth, set_password, verify_password, is_locked_out, login_required
from yaml_manager import (read_yaml, write_yaml, get_file_hash,
                          resolve_path, set_at_path, append_at_path, delete_at_path)
from backup_manager import create_backup, restore_backup, list_backups
from schemas import validate_data
from image_manager import list_images, save_image, delete_image
from build_pipeline import full_deploy, jekyll_build, smoke_test, git_push, has_unpushed_commits
from audit_log import log_event, get_recent

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE
CORS(app, origins=["http://localhost:4010"])


@app.errorhandler(413)
def _too_large(_e):
    # Without this, Flask's default 413 returns an HTML body. The CMS image
    # picker calls r.json() on the response, throws on parse, and the user
    # only sees a generic "Upload failed" toast — exactly the symptom that
    # made news image uploads look silently broken. Surfacing the limit in
    # JSON lets the picker show a clear "File too large (max 16MB)" message.
    mb = MAX_UPLOAD_SIZE // (1024 * 1024)
    return jsonify({"error": f"File too large. Maximum size: {mb}MB"}), 413


# ═══════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════

LOGIN_HTML = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Login - Reality Lab</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'Inter',sans-serif;background:#0f172a;display:flex;align-items:center;justify-content:center;min-height:100vh}
  .card{background:#1e293b;border-radius:16px;padding:48px;width:400px;box-shadow:0 25px 50px rgba(0,0,0,.5)}
  h1{color:#e2e8f0;font-size:24px;margin-bottom:8px} .sub{color:#94a3b8;font-size:14px;margin-bottom:32px}
  label{color:#cbd5e1;font-size:13px;display:block;margin-bottom:6px}
  input{width:100%;padding:12px 16px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#e2e8f0;font-size:15px;outline:none}
  input:focus{border-color:#3b82f6}
  button{width:100%;padding:12px;margin-top:24px;border:none;border-radius:8px;background:#3b82f6;color:#fff;font-size:15px;font-weight:600;cursor:pointer}
  button:hover{background:#2563eb} .error{color:#ef4444;font-size:13px;margin-top:12px;text-align:center}
  .setup-note{color:#60a5fa;font-size:13px;margin-top:8px}
</style></head><body>
<div class="card">
  <h1>Reality Lab Admin</h1>
  <p class="sub">{{ subtitle }}</p>
  <form method="POST" action="/login">
    {% if setup_mode %}
    <label>New Password</label><input type="password" name="password" placeholder="Set admin password" required>
    <label style="margin-top:16px">Confirm Password</label><input type="password" name="password_confirm" placeholder="Confirm password" required>
    <p class="setup-note">First-time setup: create your admin password</p>
    {% else %}
    <label>Your Name (편집자 이름)</label><input type="text" name="user_name" placeholder="홍길동" required autofocus>
    <label style="margin-top:16px">Password</label><input type="password" name="password" placeholder="Enter password" required>
    {% endif %}
    <button type="submit">{{ button_text }}</button>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
  </form>
</div></body></html>"""


# ═══════════════════════════════════════
# OVERLAY (injected into _site/ HTML)
# ═══════════════════════════════════════

def _load_overlay():
    """Load overlay CSS and JS from static files."""
    css_path = os.path.join(os.path.dirname(__file__), 'static', 'admin-overlay.css')
    js_path = os.path.join(os.path.dirname(__file__), 'static', 'admin-overlay.js')
    with open(css_path, 'r') as f:
        css = f.read()
    with open(js_path, 'r') as f:
        js = f.read()
    return f"""
<!-- Admin CMS Overlay -->
<style>{css}</style>

<!-- Dev Banner -->
<div class="admin-dev-banner">
  <span class="dev-label">DEV MODE</span>
  <div class="dev-right">
    <span class="admin-status" id="admin-status">Click any element to edit</span>
    <button class="apply-btn" id="admin-apply-btn" onclick="window._adminApplyChanges()">Apply to Live Site <span class="badge" id="admin-unpushed-count">0</span></button>
    <a href="#" onclick="window._adminShowAudit();return false;" class="logout-btn" style="background:transparent;color:#94a3b8;border:1px solid #334155;margin-right:6px">📋 Log</a>
    <a href="/logout" class="logout-btn">Logout</a>
  </div>
</div>

<!-- Panel backdrop -->
<div class="admin-panel-backdrop" id="admin-panel-backdrop" onclick="adminClosePanel()"></div>

<!-- Side panel -->
<div class="admin-panel" id="admin-panel">
  <div class="admin-panel-header">
    <h2 id="admin-panel-title">Edit</h2>
    <button class="admin-panel-close" onclick="adminClosePanel()">&times;</button>
  </div>
  <div class="admin-panel-body" id="admin-panel-body"></div>
</div>

<!-- Toast & Loading -->
<div class="admin-toast" id="admin-toast"></div>
<div class="admin-loading" id="admin-loading">
  <div class="admin-loading-box"><div class="admin-spinner"></div><div id="admin-loading-text">Deploying...</div></div>
</div>

<script>{js}</script>
"""


# ═══════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
def login():
    password_set = init_auth(app)
    if request.method == 'GET':
        if session.get('authenticated'):
            return redirect('/')
        return render_template_string(LOGIN_HTML,
            setup_mode=not password_set,
            subtitle="First-time setup" if not password_set else "Enter your password",
            button_text="Create Account" if not password_set else "Login",
            error=None)

    if not password_set:
        pw = request.form.get('password', '')
        pw_confirm = request.form.get('password_confirm', '')
        if len(pw) < 4:
            return render_template_string(LOGIN_HTML, setup_mode=True,
                subtitle="First-time setup", button_text="Create Account",
                error="Password must be at least 4 characters")
        if pw != pw_confirm:
            return render_template_string(LOGIN_HTML, setup_mode=True,
                subtitle="First-time setup", button_text="Create Account",
                error="Passwords do not match")
        set_password(pw)
        session.permanent = True
        session['authenticated'] = True
        return redirect('/')

    if is_locked_out():
        return render_template_string(LOGIN_HTML, setup_mode=False,
            subtitle="Enter your password", button_text="Login",
            error=f"Too many failed attempts. Locked for {LOGIN_LOCKOUT_MINUTES} minutes.")

    pw = request.form.get('password', '')
    user_name = request.form.get('user_name', '').strip() or 'Anonymous'
    if verify_password(pw):
        session.permanent = True
        session['authenticated'] = True
        session['user_name'] = user_name
        log_event(user_name, "LOGIN", "", request.headers.get('User-Agent','')[:80])
        return redirect('/')
    return render_template_string(LOGIN_HTML, setup_mode=False,
        subtitle="Enter your password", button_text="Login", error="Invalid password")


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ─── Serve _site/ with overlay injection ─────

@app.route('/')
@app.route('/<path:filepath>')
@login_required
def serve_site(filepath='index.html'):
    # API and special routes are handled by other functions
    if filepath.startswith('api/'):
        return jsonify({"error": "Not found"}), 404

    # Map clean URLs
    if filepath == '' or filepath == '/':
        filepath = 'index.html'
    elif '.' not in filepath.split('/')[-1]:
        filepath = filepath.rstrip('/') + '.html'

    full_path = os.path.join(SITE_DIR, filepath)

    if not os.path.exists(full_path):
        # Try with index.html
        alt_path = os.path.join(SITE_DIR, filepath, 'index.html')
        if os.path.exists(alt_path):
            full_path = alt_path
        else:
            return send_from_directory(SITE_DIR, '404.html'), 404

    # For HTML files, inject the overlay
    if full_path.endswith('.html'):
        with open(full_path, 'r', encoding='utf-8') as f:
            html = f.read()
        # Inject overlay before </body>
        # Rewrite absolute URLs to relative so navigation stays in dev mode
        html = html.replace('https://ssurealitylab.github.io/', '/')
        html = html.replace('https://ssurealitylab.github.io"', '/"')
        html = html.replace('https://reality.ssu.ac.kr/', '/')
        html = html.replace('https://reality.ssu.ac.kr"', '/"')
        # Inject admin overlay
        html = html.replace('</body>', _load_overlay() + '</body>')
        return Response(html, mimetype='text/html')

    # For other files (css, js, images), serve directly
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    return send_from_directory(directory, filename)


# ─── Data API ────────────────────────

@app.route('/api/data/<filename>')
@login_required
def api_get_data(filename):
    try:
        data = read_yaml(filename)
        plain = json.loads(json.dumps(_to_serializable(data)))
        return jsonify(plain)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ─── Deploy API ──────────────────────

@app.route('/api/deploy/<filename>/<path:data_path>', methods=['PUT'])
@login_required
def api_deploy_update(filename, data_path):
    try:
        new_value = request.get_json()
        if not new_value:
            return jsonify({"error": "No data provided"}), 400
        # Drop null/incomplete slide entries before saving. Without this,
        # a buggy client-side Move (e.g. idx out of range → splice returns
        # [undefined] → JSON serializes as null) silently corrupted the
        # YAML and the More Images modal rendered broken tiles for each
        # null entry.
        if isinstance(new_value, list) and (
            data_path.endswith('.slider') or data_path.endswith('.slider_archive')
        ):
            new_value = [
                s for s in new_value
                if s and isinstance(s, dict) and s.get('image') and s.get('title')
            ]
        errors = validate_data(filename, new_value, path=data_path)
        if errors:
            return jsonify({"status": "error", "errors": errors})
        data = read_yaml(filename)
        set_at_path(data, data_path, new_value)
        editor = session.get('user_name', 'Anonymous')
        result = full_deploy(filename, data, f"Update {filename}/{data_path} (by {editor})")
        log_event(editor, "UPDATE", f"{filename}/{data_path}", result.get('message',''))
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/deploy/<filename>/<path:data_path>', methods=['POST'])
@login_required
def api_deploy_add(filename, data_path):
    try:
        new_value = request.get_json()
        if not new_value:
            return jsonify({"error": "No data provided"}), 400
        errors = validate_data(filename, new_value, path=data_path)
        if errors:
            return jsonify({"status": "error", "errors": errors})
        data = read_yaml(filename)
        if (filename == 'news' and data_path == 'news') or \
           (filename == 'publications' and data_path == 'publications') or \
           (filename == 'domestic_publications' and data_path == 'publications'):
            target = resolve_path(data, data_path)
            target.insert(0, new_value)
        else:
            append_at_path(data, data_path, new_value)
        editor = session.get('user_name', 'Anonymous')
        result = full_deploy(filename, data, f"Add to {filename}/{data_path} (by {editor})")
        log_event(editor, "ADD", f"{filename}/{data_path}", result.get('message',''))
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/deploy/<filename>/<path:data_path>', methods=['DELETE'])
@login_required
def api_deploy_delete(filename, data_path):
    try:
        data = read_yaml(filename)
        delete_at_path(data, data_path)
        editor = session.get('user_name', 'Anonymous')
        result = full_deploy(filename, data, f"Delete {filename}/{data_path} (by {editor})")
        log_event(editor, "DELETE", f"{filename}/{data_path}", result.get('message',''))
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ─── User info ───────────────────────

@app.route('/api/whoami')
@login_required
def api_whoami():
    return jsonify({"name": session.get('user_name', 'Anonymous')})


# ─── Image API ───────────────────────

@app.route('/api/images/<category>')
@login_required
def api_list_images(category):
    return jsonify(list_images(category))


@app.route('/api/images/<category>/upload', methods=['POST'])
@login_required
def api_upload_image(category):
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        result = save_image(request.files['file'], category)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ─── Backup API ──────────────────────

@app.route('/api/backups')
@login_required
def api_list_backups():
    return jsonify(list_backups())


@app.route('/api/backups/<backup_id>/restore', methods=['POST'])
@login_required
def api_restore_backup(backup_id):
    if restore_backup(backup_id):
        success, output = jekyll_build()
        return jsonify({"status": "success", "message": f"Restored. Build: {'OK' if success else 'Failed'}"})
    return jsonify({"status": "error", "message": "Backup not found"})


# ─── Build & RAG API ────────────────

@app.route('/api/push', methods=['POST'])
@login_required
def api_push():
    """Push all local commits to remote (apply to live site)."""
    success, output = git_push()
    editor = session.get('user_name', 'Anonymous')
    log_event(editor, "APPLY (push)", "", output[:120])
    if success:
        return jsonify({"status": "success", "message": output})
    return jsonify({"status": "error", "message": output})


@app.route('/api/audit')
@login_required
def api_audit():
    """Get recent audit log entries."""
    limit = int(request.args.get('limit', 100))
    return jsonify(get_recent(limit))


@app.route('/api/unpushed')
@login_required
def api_unpushed():
    """Check for unpushed commits."""
    return jsonify(has_unpushed_commits())


@app.route('/api/build', methods=['POST'])
@login_required
def api_build():
    success, output = jekyll_build()
    if success:
        return jsonify({"status": "success", "message": "Build completed"})
    return jsonify({"status": "error", "message": output})


@app.route('/api/rag/update', methods=['POST'])
@login_required
def api_update_rag():
    import subprocess
    try:
        result = subprocess.run(
            ["/bin/bash", os.path.join(SITE_ROOT, "ai_server", "update_rag.sh")],
            capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return jsonify({"status": "success", "message": "RAG updated"})
        return jsonify({"status": "error", "message": result.stderr})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ─── Helpers ─────────────────────────

def _to_serializable(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    if hasattr(obj, 'items'):
        return {str(k): _to_serializable(v) for k, v in obj.items()}
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
        return [_to_serializable(item) for item in obj]
    elif hasattr(obj, '__str__') and type(obj).__name__ in ('ScalarFloat', 'ScalarInt', 'ScalarBoolean'):
        if type(obj).__name__ == 'ScalarBoolean': return bool(obj)
        if type(obj).__name__ == 'ScalarInt': return int(obj)
        return float(obj)
    return obj


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Reality Lab Admin CMS')
    parser.add_argument('--port', type=int, default=CMS_PORT)
    parser.add_argument('--host', type=str, default='0.0.0.0')
    args = parser.parse_args()
    init_auth(app)
    print(f"\n{'='*50}")
    print(f"  Reality Lab Admin CMS")
    print(f"  http://localhost:{args.port}")
    print(f"{'='*50}\n")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
