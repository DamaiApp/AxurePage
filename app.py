from flask import Flask, request, jsonify
import os
import zipfile
import shortuuid
import git
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 設定 GitHub Pages Repo
GITHUB_REPO = "DamaiApp/damaiapp.github.io"
BASE_URL = f"https://damaiapp.github.io/projects/"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # 用環境變數

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/status/<project_id>", methods=["GET"])
def check_deployment_status(project_id):
    """
    檢查 GitHub Pages 是否已經部署成功
    """
    project_url = f"{BASE_URL}{project_id}/index.html"

    try:
        response = requests.get(project_url, timeout=5)
        if response.status_code == 200:
            return jsonify({"status": "success", "url": project_url})
        else:
            return jsonify({"status": "pending"})
    except requests.exceptions.RequestException:
        return jsonify({"status": "pending"})

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "沒有上傳檔案"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "檔案名稱錯誤"}), 400

    # 取得安全的檔名
    filename = secure_filename(file.filename)
    project_id = shortuuid.uuid()[:8]  # 生成 8 位短網址
    zip_path = os.path.join(UPLOAD_FOLDER, filename)

    # 儲存 ZIP
    file.save(zip_path)

    # 解壓縮 ZIP
    extract_path = os.path.join(UPLOAD_FOLDER, "projects", project_id)
    os.makedirs(extract_path, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    # 刪除 ZIP
    os.remove(zip_path)

    # **確保 index.html 在根目錄**
    root_html_folder = find_root_html_folder(extract_path)

    if root_html_folder is None:
        return jsonify({"error": "未找到 index.html，請檢查 ZIP 內容"}), 400

    # Push 到 GitHub Pages
    success = push_to_github(root_html_folder, project_id)
    if not success:
        return jsonify({"error": "Push 到 GitHub 失敗"}), 500

    # 生成 GitHub Pages 網址
    access_url = f"{BASE_URL}{project_id}/index.html"
    return jsonify({"message": "上傳成功", "url": access_url, "project_id": project_id})


def find_root_html_folder(folder_path):
    """
    遞迴尋找 index.html 所在的根目錄
    """
    while True:
        files = os.listdir(folder_path)
        if "index.html" in files:
            return folder_path  # 已經是正確的 HTML 目錄

        # 如果只有一個資料夾，且沒有 index.html，則進入該資料夾
        subfolders = [f for f in files if os.path.isdir(os.path.join(folder_path, f))]
        if len(subfolders) == 1:
            folder_path = os.path.join(folder_path, subfolders[0])
        else:
            break  # 找不到 index.html

    return None


def push_to_github(folder_path, project_id):
    """
    把 Axure HTML Push 到 GitHub
    """
    repo_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
    local_repo = "/tmp/github_repo"

    # Clone Repo
    if os.path.exists(local_repo):
        os.system(f"rm -rf {local_repo}")
    git.Repo.clone_from(repo_url, local_repo)

    # 複製 Axure HTML 檔案
    target_path = os.path.join(local_repo, "projects", project_id)
    os.system(f"mkdir -p {target_path}")
    os.system(f"cp -r {folder_path}/* {target_path}")

    # Git Commit & Push
    try:
        repo = git.Repo(local_repo)
        repo.git.add(A=True)
        repo.index.commit(f"Deploy Axure project {project_id}")
        repo.remote(name="origin").push()
        return True
    except Exception as e:
        print("Git Push 失敗:", str(e))
        return False

# 讓 Flask 自動讀取 Cloud Run 指定的埠號
port = int(os.environ.get("PORT", 8080))
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)