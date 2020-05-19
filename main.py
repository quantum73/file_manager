import re
import socket
from flask import render_template, request, send_from_directory, redirect
from werkzeug.utils import secure_filename
from pathlib import Path
from config import *


MY_IP = socket.gethostbyname(socket.getfqdn())


@app.route('/', methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
@check_and_transform_path
def dir_viewer(path=None):
    entries = os.scandir(path)
    prev_dir = None
    flag_exists = None
    upload_flag = None
    tag = None
    json_data = read_json(JSON_PATH)

    if path and path != TOP_DIR:
        temp = list(map(str, Path(TOP_DIR).rglob(path.split('\\')[-1])))[0]
        prev_dir = temp.split('\\')[-1]
        prev_dir = re.sub(rf'\b{prev_dir}', '', temp)

    if request.method == 'POST':
        tag = request.form.get('tag')

        if 'home' in request.form:
            return redirect('/')

        if 'edit_desc' in request.form:
            curr_key = request.form.get('edit_desc')
            
            edit_desc_key(curr_key)
            
            return redirect(f'/{path}')

        if 'add_desc' in request.form:
            description = request.form.get('description')
            curr_key = request.form.get('add_desc')
            
            write_desc_key(curr_key, description)
            
            return redirect(f'/{path}')
        
        if 'delete_img' in request.form:
            curr_key = request.form.get('delete_img')
            
            delete_img(curr_key, path)
            
            return redirect(f'/{path}')
        
        if 'add_img' in request.form:
            curr_path = request.form.get('add_img')
            if '^' in curr_path:
                new_name = curr_path.split('^')[-1].replace('.txt', '')
                new_name = new_name.split('.')[0]
            else:
                new_name = curr_path.split('/')[-1].split('.')[0]
            files = request.files.getlist("preview_img")
            for el in files:
                if bool(el.filename):
                    file = el
                    break

            if file and check_image(file.filename):
                filename = secure_filename(file.filename)
                filename = new_name + '.' + filename.split('.')[-1]
                img_path = path.replace(DATA_FOLDER, IMG_FOLDER)
                if not os.path.exists(img_path):
                    os.makedirs(img_path)
                file.save(os.path.join(img_path, filename))
                write_img_key(curr_path, filename)
            
            return redirect(f'/{path}')

        if 'add_buffer_link' in request.form:
            buffer_link = request.form.get('buffer_link')
            buffer_link = buffer_link.replace('\\', '^')
            buffer_link = buffer_link.replace(' ', '_')
            link_path = os.path.join(path, f'{buffer_link}.txt')

            with open(link_path, "w") as f:
                f.write("")

            write_in_json(link_path.replace('\\', '/'))

            return redirect(f'/{path}')
        
        if request.form.get('delete'):
            current_name = request.form.get('delete')
            print('delete path =', current_name)
            delete_path = list(map(str, Path(path).rglob(current_name)))[0]
            delete_from_json(delete_path)

            if os.path.isdir(delete_path):
                shutil.rmtree(delete_path)
            else:
                os.remove(delete_path)

            return redirect(f'/{path}')

        if 'new_folder' in request.form:
            folder = request.form.get('folder')
            paths_list = list(map(str, Path(path).rglob(folder)))

            if paths_list:
                flag_exists = 'Exists'
                prev_dir = re.sub(rf'\b{folder}', '', paths_list[0])
                entries = os.scandir(prev_dir)
                return render_template("start.html", entries=entries, prev_dir=prev_dir,
                                       flag_exists=flag_exists, tag_name=folder, json_data=json_data)
            else:
                os.mkdir(os.path.join(path, folder))
                return redirect(f'/{path}')

        if 'search_tag' in request.form:
            tag = request.form.get('search_label')
            paths_list = list(map(str, Path(TOP_DIR).rglob(tag)))

            if paths_list:
                prev_dir = re.sub(rf'\b{tag}', '', paths_list[0])
                return redirect(f'/{prev_dir}')
            else:
                flag_exists = 'Not exists'
                return render_template("start.html", entries=entries, prev_dir=prev_dir,
                                       flag_exists=flag_exists, tag_name=tag, json_data=json_data)

        if 'search_desc' in request.form:
            desc_flag = 'Not Exists'
            find_desc = request.form.get('search_label')
            
            for key, val in json_data.items():
                if find_desc in val["description"]:
                    prev_dir = key.replace('/', '\\')
                    prev_dir = prev_dir.replace(TOP_DIR, '').strip('\\/')
                    prev_dir = os.path.join(TOP_DIR, *prev_dir.split('\\')[:-1])
                    return redirect(f'/{prev_dir}')

            return render_template("start.html", entries=entries, prev_dir=prev_dir,
                                   desc_flag=desc_flag, json_data=json_data)

        if 'upload' in request.form:
            file = request.files.getlist("file")[0]
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(path, filename))
                key = os.path.join(path, filename).replace('\\', '/')
                write_in_json(key)
                return redirect(f'/{path}')
            else:
                upload_flag = 'Not Exists'
                return render_template("start.html", entries=entries, prev_dir=prev_dir,
                                       upload_flag=upload_flag, json_data=json_data)

    json_data = read_json(JSON_PATH)

    return render_template("start.html", entries=entries, prev_dir=prev_dir, flag_exists=flag_exists,
                           tag_name=tag, json_data=json_data, upload_flag=upload_flag)


@app.route("/download/<path:filename>", methods=['GET', 'POST'])
def download(filename):
    uploads = list(map(str, Path(TOP_DIR).rglob(filename)))[0]
    uploads = uploads.replace(filename, '')
    return send_from_directory(directory=uploads, filename=filename)


if __name__ == '__main__':
    app.run(host=MY_IP, threaded=True)
