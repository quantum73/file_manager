import os
from functools import wraps
import json
from flask import Flask, abort
import shutil

DATA_FOLDER = 'data'
IMG_FOLDER = 'img'
IMG_DIR = os.path.join(os.getcwd(), IMG_FOLDER)
app = Flask(__name__, static_folder=IMG_FOLDER)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
TOP_DIR = os.path.join(app.root_path, DATA_FOLDER)
DB_DIR = os.path.join(app.root_path, 'db')
JSON_PATH = os.path.join(DB_DIR, 'files.json')
IMG_EXTENSIONS = ['png', 'jpg', 'jpeg', 'bmp']
ALLOWED_EXTENSIONS = ['obj', 'zip', 'rar', 'blend', 'fbx']

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)
if not os.path.exists(TOP_DIR):
    os.makedirs(TOP_DIR)
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)


def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def read_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(path, "w") as f:
            json.dump({}, f)


def write_in_json(key, val=None):
    data = read_json(JSON_PATH)
    if val is None:
        data[key] = {"img_name": "no_img", "description": "no_desc", "show_edit": "on"}
    else:
        data[key] = {"img_name": val, "description": "no_desc", "show_edit": "on"}

    with open(JSON_PATH, "w") as f:
        json.dump(data, f)


def edit_desc_key(curr_key):
    curr_key = curr_key.replace('\\', '/')
    data = read_json(JSON_PATH)

    for key, val in data.items():
        if curr_key in key:
            val["show_edit"] = "off"

    with open(JSON_PATH, "w") as f:
        json.dump(data, f)


def write_desc_key(curr_key, description):
    curr_key = curr_key.replace('\\', '/')
    data = read_json(JSON_PATH)

    for key, val in data.items():
        if curr_key in key:
            val["description"] = description
            val["show_edit"] = "on"

    with open(JSON_PATH, "w") as f:
        json.dump(data, f)


def write_img_key(path, img_name):
    path = path.replace('\\', '/')
    data = read_json(JSON_PATH)

    for key, val in data.items():
        if path in key:
            val["img_name"] = img_name

    with open(JSON_PATH, "w") as f:
        json.dump(data, f)


def delete_img(curr_key, path):
    data = read_json(JSON_PATH)
    path = path.replace('\\', '/')

    for key, val in data.items():
        if curr_key in key and val["img_name"] != "no_img":
            img_delete_path = path.replace(DATA_FOLDER, IMG_FOLDER)
            img_delete_path = os.path.join(img_delete_path, val["img_name"])
            os.remove(img_delete_path)
            val["img_name"] = "no_img"

    with open(JSON_PATH, "w") as f:
        json.dump(data, f)


def delete_from_json(path):
    data = read_json(JSON_PATH)
    key = [i for i in data.keys() if path.replace('\\', '/') in i]

    if key:
        val = data[key[0]]
        if val["img_name"] != "no_img":
            img_delete_path = os.path.join(IMG_FOLDER, val["img_name"])
            os.remove(img_delete_path)
        del data[key[0]]
    if os.path.isdir(path.replace(DATA_FOLDER, IMG_FOLDER)):
        shutil.rmtree(path.replace(DATA_FOLDER, IMG_FOLDER))

    with open(JSON_PATH, "w") as f:
        json.dump(data, f)


def check_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in IMG_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def normalize_path(path, follow_symlinks=True):
    if follow_symlinks:
        return os.path.realpath(path)
    return os.path.abspath(path)


def is_safe_path(basedir, path):
    return path.startswith(basedir)


def check_and_transform_path(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        path = normalize_path(kwargs.get("path", TOP_DIR))
        if not is_safe_path(TOP_DIR, path) or not os.path.exists(path):
            abort(404)
        kwargs["path"] = path
        return f(*args, **kwargs)

    return wrapper
