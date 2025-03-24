# Copyright 2016 Henry Zhou (http://www.maxodoo.com)
# Copyright 2016 Rodney (http://clearcorp.cr/)
# Copyright 2012 Agile Business Group
# Copyright 2012 Therp BV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import os
import subprocess
import platform
from email.policy import default
import pyzipper
import threading
import xlsxwriter
import odoo.http as http
from dataclasses import fields
from odoo.http import request
from odoo.addons.web.controllers.main import ExcelExport
import shutil

DOWNLOADS_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")


def create_excel_file(file_path, headers, rows):
    try:
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        for row_num, row in enumerate(rows, start=1):
            for col_num, cell_value in enumerate(row):
                worksheet.write(row_num, col_num, cell_value)

        workbook.close()
        return True
    except Exception as e:
        print(f"Error creating Excel file: {e}")
        return False


def compress_and_encrypt_file(file_path, archive_path, ui_password, folder_path):
    try:
        if not file_path or not os.path.exists(file_path):
            print("No valid file to compress.")
            return False

        file_name = os.path.basename(file_path)
        system_platform = platform.system()

        if system_platform == "Linux":
              # Escape parentheses and spaces in file/folder names
            safe_folder_path = folder_path.replace("(", r"\(").replace(")", r"\)").replace(" ", r"\ ")
            safe_archive_path = archive_path.replace("(", r"\(").replace(")", r"\)").replace(" ", r"\ ")
            safe_file_name = file_name.replace("(", r"\(").replace(")", r"\)").replace(" ", r"\ ")

            command = f"cd {safe_folder_path} && zip -j -e --password '{ui_password}' {safe_archive_path} {safe_file_name}"
            print(f"Executing ZIP command: {command}")

            result = subprocess.run(command, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

            if result.returncode != 0:
                print(f"ZIP command failed: {result.stderr}")
                return False

        elif system_platform == "Windows":
            with pyzipper.AESZipFile(archive_path, 'w', compression=pyzipper.ZIP_DEFLATED,
                                     encryption=pyzipper.WZ_AES) as zipf:
                zipf.setpassword(ui_password.encode('utf-8'))
                zipf.write(file_path, arcname=file_name)

        else:
            print("Unsupported OS")
            return False

        if os.path.exists(archive_path):
            return True
        else:
            return False

    except subprocess.CalledProcessError as e:
        return False
    except Exception as e:
        return False

def delete_folder_permanently(folder_path):
    try:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)  #permanently folder will be deleted
        else:
            print(f"Folder '{folder_path}' does not exist.")
    except Exception as e:
        print(f"Error deleting folder: {e}")

class ExcelExportView(ExcelExport):
    def __getattribute__(self, name):
        if name == 'fmt':
            raise AttributeError()
        return super(ExcelExportView, self).__getattribute__(name)

    @http.route('/web/export/xls_view', type='http', auth='user')
    def export_xls_view(self, data, token):
        data = json.loads(data)
        model = data.get('model', [])
        columns_headers = data.get('headers', [])
        rows = data.get('rows', [])
        ui_password = data.get('password', '')
        company_pass = request.env.user.company_id.stored_password
        ui_password = company_pass if company_pass else ui_password
        print(f"Received export request for model: {model}, with password: {ui_password}")

        # Ensure unique folder and ZIP file names
        file_base_name = model or "ExportedFile"
        counter = 0

        while True:
            file_name_count = f"{file_base_name} ({counter})" if counter > 0 else file_base_name
            folder_path = os.path.join(DOWNLOADS_FOLDER, file_name_count)
            file_name_zip = f"{file_name_count}.zip"
            archive_path = os.path.join(DOWNLOADS_FOLDER, file_name_zip)

            # Ensure both folder and ZIP file are unique
            if not os.path.exists(folder_path) and not os.path.exists(archive_path):
                os.makedirs(folder_path, exist_ok=True)
                break

            counter += 1

        excel_file_name = f"{file_name_count}.xlsx"
        excel_file_path = os.path.join(folder_path, excel_file_name)
        # Create Excel file
        if not create_excel_file(excel_file_path, columns_headers, rows):
            return request.make_response("Error: Could not create Excel file", status=500)

        # Find latest Excel file
        xlsx_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".xlsx")]
        latest_file = max(xlsx_files, key=os.path.getmtime) if xlsx_files else None

        if not latest_file:
            return request.make_response("Error: No Excel file found for compression", status=500)

        # Compress and encrypt file
        success = compress_and_encrypt_file(latest_file, archive_path, ui_password, folder_path)
        if not success:
            return request.make_response("Error: Could not create the zip file", status=500)

        # Ensure ZIP file exists before sending response
        if not os.path.exists(archive_path):
            return request.make_response("Error: ZIP file was not created", status=500)

        # Read ZIP data
        with open(archive_path, 'rb') as f:
            zip_data = f.read()

        # Delete the folder in a separate thread
        threading.Thread(target=delete_folder_permanently, args=(folder_path,), daemon=True).start()

        # Return ZIP file as response
        return request.make_response(
            zip_data,
            headers=[
                ('Content-Disposition', f"attachment; filename={file_name_zip}"),
                ('Content-Type', 'application/zip')
            ],
            cookies={'fileToken': token}
        )


    @http.route('/web/export/get_allowed_models', type='json', auth='user')
    def get_allowed_models(self):
        # Fetch the latest configuration settings
        config_group_records = request.env['res.config.settings'].sudo().search([], order='create_date desc',
                                                                                limit=1)

        # Get restricted models
        mode_restrict = [group.model.strip() for groups in config_group_records for group in
                         groups.xlsx_model_restrict
                         if group.model]

        return mode_restrict