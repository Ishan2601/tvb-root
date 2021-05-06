# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2020, Baycrest Centre for Geriatric Care ("Baycrest") and others
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#
"""
This module is an interface for the tvb storage module.
All calls to methods from this module must be done through this class.

.. moduleauthor:: Robert Vincze <robert.vincze@codemart.ro>
"""

from datetime import datetime
import os

from tvb.basic.logger.builder import get_logger
from tvb.basic.profile import TvbProfile
from tvb.storage.h5.encryption.data_encryption_handler import DataEncryptionHandler, FoldersQueueConsumer, \
    encryption_handler
from tvb.storage.h5.encryption.encryption_handler import EncryptionHandler
from tvb.storage.h5.file.exceptions import RenameWhileSyncEncryptingException
from tvb.storage.h5.file.files_helper import FilesHelper, TvbZip
from tvb.storage.h5.file.hdf5_storage_manager import HDF5StorageManager
from tvb.storage.h5.file.xml_metadata_handlers import XMLReader, XMLWriter


class StorageInterface:
    TEMP_FOLDER = "TEMP"
    IMAGES_FOLDER = "IMAGES"
    PROJECTS_FOLDER = "PROJECTS"

    ROOT_NODE_PATH = "/"
    TVB_FILE_EXTENSION = XMLWriter.FILE_EXTENSION
    TVB_STORAGE_FILE_EXTENSION = ".h5"
    TVB_ZIP_FILE_EXTENSION = ".zip"

    TVB_PROJECT_FILE = "Project" + TVB_FILE_EXTENSION

    ZIP_FILE_EXTENSION = "zip"

    logger = get_logger(__name__)

    def __init__(self):
        self.files_helper = FilesHelper()
        self.data_encryption_handler = encryption_handler
        self.folders_queue_consumer = FoldersQueueConsumer()

        # object attributes which have parameters in their constructor will be lazily instantiated
        self.tvb_zip = None
        self.storage_manager = None
        self.xml_reader = None
        self.xml_writer = None
        self.encryption_handler = None

    # FilesHelper methods start here #

    def check_created(self, path=TvbProfile.current.TVB_STORAGE):
        self.files_helper.check_created(path)

    @staticmethod
    def get_projects_folder():
        return FilesHelper.get_projects_folder()

    def get_project_folder(self, project_name, *sub_folders):
        return self.files_helper.get_project_folder(project_name, *sub_folders)

    def get_temp_folder(self, project_name):
        return self.files_helper.get_project_folder(project_name, self.TEMP_FOLDER)

    @staticmethod
    def get_project_folder_from_h5(h5_file):
        return FilesHelper.get_project_folder_from_h5(h5_file)

    def rename_project_structure(self, project_name, new_name):
        return self.files_helper.rename_project_structure(project_name, new_name)

    def remove_project_structure(self, project_name):
        self.files_helper.remove_project_structure(project_name)

    def get_project_meta_file_path(self, project_name):
        return self.files_helper.get_project_meta_file_path(project_name)

    def read_project_metadata(self, project_path):
        return FilesHelper.read_project_metadata(project_path, self.TVB_PROJECT_FILE)

    def write_project_metadata_from_dict(self, project_path, meta_entity):
        FilesHelper.write_project_metadata_from_dict(project_path, meta_entity, self.TVB_PROJECT_FILE)

    def write_project_metadata(self, meta_dictionary):
        self.files_helper.write_project_metadata(meta_dictionary, self.TVB_PROJECT_FILE)

    def get_operation_folder(self, project_name, operation_id):
        return self.files_helper.get_operation_folder(project_name, operation_id)

    def remove_operation_data(self, project_name, operation_id):
        self.files_helper.remove_operation_data(project_name, operation_id)

    def remove_datatype_file(self, h5_file):
        self.files_helper.remove_datatype_file(h5_file)
        self.push_folder_to_sync(self.get_project_folder_from_h5(h5_file))

    def move_datatype(self, new_project_name, new_op_id, full_path):
        self.files_helper.move_datatype(new_project_name, new_op_id, full_path)

    def get_images_folder(self, project_name):
        return self.files_helper.get_images_folder(project_name, self.IMAGES_FOLDER)

    def write_image_metadata(self, figure, meta_entity):
        self.files_helper.write_image_metadata(figure, meta_entity, self.IMAGES_FOLDER)

    def remove_image_metadata(self, figure):
        self.files_helper.remove_image_metadata(figure, self.IMAGES_FOLDER)

    def get_allen_mouse_cache_folder(self, project_name):
        return self.get_allen_mouse_cache_folder(project_name)

    def zip_folders(self, all_datatypes, project_name, zip_full_path, folder_prefix=""):
        operation_folders = []
        for data_type in all_datatypes:
            operation_folder = self.get_operation_folder(project_name, data_type.fk_from_operation)
            operation_folders.append(operation_folder)
        FilesHelper.zip_folders(zip_full_path, operation_folders, folder_prefix)

    @staticmethod
    def zip_folder(result_name, folder_root):
        FilesHelper.zip_folder(result_name, folder_root)

    def unpack_zip(self, uploaded_zip, folder_path):
        return self.files_helper.unpack_zip(uploaded_zip, folder_path)

    @staticmethod
    def copy_file(source, dest, dest_postfix=None, buffer_size=1024 * 1024):
        FilesHelper.copy_file(source, dest, dest_postfix, buffer_size)

    @staticmethod
    def remove_files(file_list, ignore_exception=False):
        FilesHelper.remove_files(file_list, ignore_exception)

    @staticmethod
    def remove_folder(folder_path, ignore_errors=False):
        FilesHelper.remove_folder(folder_path, ignore_errors)

    @staticmethod
    def compute_size_on_disk(file_path):
        return FilesHelper.compute_size_on_disk(file_path)

    @staticmethod
    def compute_recursive_h5_disk_usage(start_path='.'):
        return FilesHelper.compute_recursive_h5_disk_usage(start_path)

    # TvbZip methods start here #
    def initialize_tvb_zip(self, dest_path, mode="r"):
        self.tvb_zip = TvbZip(dest_path, mode)

    def write_zip_folder(self, folder, archive_path_prefix="", exclude=[]):
        self.tvb_zip.write_zip_folder(folder, archive_path_prefix, exclude)

    def write_zip_folders(self, folders, archive_path_prefix="", exclude=[]):
        self.tvb_zip.write_zip_folders(folders, archive_path_prefix, exclude)

    def unpack_zip(self, uploaded_zip, folder_path):
        self.initialize_tvb_zip(uploaded_zip)
        unpacked_folder = self.tvb_zip.unpack_zip(folder_path)
        self.close_tvb_zip()
        return unpacked_folder

    def namelist(self, dest_path, mode="r"):
        self.initialize_tvb_zip(dest_path, mode)
        name_list = self.tvb_zip.namelist()
        self.close_tvb_zip()
        return name_list

    def open_tvb_zip(self, name):
        return self.tvb_zip.open(name)

    def close_tvb_zip(self):
        self.tvb_zip.close()

    def write_zip_arc(self, file_name, arc):
        return self.tvb_zip.write(file_name, arc)

    # HDF5 Storage Manager methods start here #

    def is_valid_tvb_file(self, file_full_path):
        self.storage_manager = HDF5StorageManager(file_full_path)
        return self.storage_manager.is_valid_tvb_file()

    def store_data(self, file_full_path, dataset_name, data_list, where=ROOT_NODE_PATH):
        self.storage_manager = HDF5StorageManager(file_full_path)
        self.storage_manager.store_data(dataset_name, data_list, where)

    def append_data(self, file_full_path, dataset_name, data_list, grow_dimension=1, close_file=True):
        self.storage_manager = HDF5StorageManager(file_full_path)
        self.storage_manager.append_data(dataset_name, data_list, grow_dimension, close_file, self.ROOT_NODE_PATH)

    def remove_data(self, file_full_path, dataset_name):
        self.storage_manager = HDF5StorageManager(file_full_path)
        self.storage_manager.remove_data(dataset_name, self.ROOT_NODE_PATH)

    def get_data(self, file_full_path, dataset_name, data_slice=None,
                 where=ROOT_NODE_PATH, ignore_errors=False,
                 close_file=True):
        self.storage_manager = HDF5StorageManager(file_full_path)
        return self.storage_manager.get_data(dataset_name, data_slice, where, ignore_errors, close_file)

    def get_data_shape(self, file_full_path, dataset_name):
        self.storage_manager = HDF5StorageManager(file_full_path)
        return self.storage_manager.get_data_shape(dataset_name, self.ROOT_NODE_PATH)

    def set_metadata(self, file_full_path, meta_dictionary, dataset_name='', tvb_specific_metadata=True,
                     where=ROOT_NODE_PATH):
        self.storage_manager = HDF5StorageManager(file_full_path)
        return self.storage_manager.set_metadata(meta_dictionary, dataset_name, tvb_specific_metadata, where)

    @staticmethod
    def serialize_bool(value):
        return HDF5StorageManager.serialize_bool(value)

    def get_metadata(self, file_full_path, dataset_name=''):
        self.storage_manager = HDF5StorageManager(file_full_path)
        return self.storage_manager.get_metadata(dataset_name, self.ROOT_NODE_PATH)

    def remove_metadata(self, file_full_path, meta_key, dataset_name='',
                        tvb_specific_metadata=True):
        self.storage_manager = HDF5StorageManager(file_full_path)
        return self.storage_manager.remove_metadata(meta_key, dataset_name, tvb_specific_metadata, self.ROOT_NODE_PATH)

    def get_file_data_version(self, file_full_path, data_version, dataset_name=''):
        self.storage_manager = HDF5StorageManager(file_full_path)
        return self.storage_manager.get_file_data_version(data_version, dataset_name, self.ROOT_NODE_PATH)

    def close_file(self, file_full_path):
        self.storage_manager = HDF5StorageManager(file_full_path)
        return self.storage_manager.close_file()

    # XML methods start here #

    def read_metadata(self, xml_path):
        self.xml_reader = XMLReader(xml_path)
        return self.xml_reader.read_metadata()

    def parse_xml_content_to_dict(self, xml_data):
        return self.xml_reader.parse_xml_content_to_dict(xml_data)

    def write_metadata(self, entity, final_path):
        self.xml_writer = XMLWriter(entity)
        return self.xml_writer.write_metadata(final_path)

    # Encryption Handler methods start here #

    def cleanup(self, dir_gid):
        self.encryption_handler = EncryptionHandler(dir_gid)
        self.encryption_handler.cleanup()

    @staticmethod
    def generate_random_password(pass_size):
        return EncryptionHandler.generate_random_password(pass_size)

    def get_encrypted_dir(self, dir_gid):
        self.encryption_handler = EncryptionHandler(dir_gid)
        return self.encryption_handler.get_encrypted_dir()

    def get_password_file(self, dir_gid):
        self.encryption_handler = EncryptionHandler(dir_gid)
        return self.encryption_handler.get_password_file()

    def encrypt_inputs(self, dir_gid, files_to_encrypt, subdir=None):
        self.encryption_handler = EncryptionHandler(dir_gid)
        return self.encryption_handler.encrypt_inputs(files_to_encrypt, subdir)

    def decrypt_results_to_dir(self, dir_gid, dir, from_subdir=None):
        self.encryption_handler = EncryptionHandler(dir_gid)
        return self.encryption_handler.decrypt_results_to_dir(dir, from_subdir)

    def decrypt_files_to_dir(self, dir_gid, files, dir):
        self.encryption_handler = EncryptionHandler(dir_gid)
        return self.encryption_handler.decrypt_files_to_dir(files, dir)

    def get_current_enc_dirname(self, dir_gid):
        self.encryption_handler = EncryptionHandler(dir_gid)
        return self.encryption_handler.current_enc_dirname

    # Data Encryption Handler methods start here #

    def inc_project_usage_count(self, folder):
        return self.data_encryption_handler.inc_project_usage_count(folder)

    def inc_running_op_count(self, folder):
        return self.data_encryption_handler.inc_running_op_count(folder)

    def dec_running_op_count(self, folder):
        return self.data_encryption_handler.dec_running_op_count(folder)

    def check_and_delete(self, folder):
        return self.data_encryption_handler.check_and_delete(folder)

    def is_in_usage(self, project_folder):
        return self.data_encryption_handler.is_in_usage(project_folder)

    @staticmethod
    def compute_encrypted_folder_path(current_project_folder):
        return DataEncryptionHandler.compute_encrypted_folder_path(current_project_folder)

    @staticmethod
    def sync_folders(folder):
        DataEncryptionHandler.sync_folders(folder)

    def set_project_active(self, project, linked_dt=None):
        self.data_encryption_handler.set_project_active(project, linked_dt)

    def set_project_inactive(self, project):
        self.data_encryption_handler.set_project_inactive(project)

    def push_folder_to_sync(self, project_name):
        project_folder = self.get_project_folder(project_name)
        self.data_encryption_handler.push_folder_to_sync(project_folder)

    @staticmethod
    def encryption_enabled():
        return DataEncryptionHandler.encryption_enabled()

    @staticmethod
    def startup_cleanup():
        return DataEncryptionHandler.startup_cleanup()

    @staticmethod
    def project_key_path(project_name):
        return DataEncryptionHandler.project_key_path(project_name)

    # Folders Queue Consumer methods start here #

    def run(self):
        return self.folders_queue_consumer.run()

    def start(self):
        self.folders_queue_consumer.start()

    def mark_stop(self):
        self.folders_queue_consumer.mark_stop()

    def join(self):
        self.folders_queue_consumer.join()

    # Export related methods start here #

    def export_datatypes(self, paths, operation):
        op_folder = self.get_operation_folder(operation.project.name, operation.id)
        op_folder_name = os.path.basename(op_folder)

        # add linked datatypes to archive in the import operation
        for pth in paths:
            zip_pth = op_folder_name + '/' + os.path.basename(pth)
            self.write_zip_arc(pth, zip_pth)

        # remove these files, since we only want them in export archive
        self.remove_folder(op_folder)

    def export_linked_datatypes(self, project_name, op_id, linked_paths):
        op_folder = self.files_helper.get_operation_folder(project_name, op_id)
        op_folder_name = os.path.basename(op_folder)

        # add linked datatypes to archive in the import operation
        for pth in linked_paths:
            zip_pth = op_folder_name + '/' + os.path.basename(pth)
            self.write_zip_arc(pth, zip_pth)

    def build_data_export_folder(self, data, export_folder):
        now = datetime.now()
        date_str = "%d-%d-%d_%d-%d-%d_%d" % (now.year, now.month, now.day, now.hour,
                                             now.minute, now.second, now.microsecond)
        tmp_str = date_str + "@" + data.gid
        data_export_folder = os.path.join(export_folder, tmp_str)
        self.check_created(data_export_folder)

        return data_export_folder

    def export_project(self, project, project_datatypes, folders_to_exclude, export_folder, linked_paths, op,
                       optimize_size):
        project_folder = self.get_project_folder(project.name)
        to_be_exported_folders = []
        considered_op_ids = []

        if optimize_size:
            # take only the DataType with visibility flag set ON
            for dt in project_datatypes:
                op_id = dt.fk_from_operation
                if op_id not in considered_op_ids:
                    to_be_exported_folders.append({'folder': self.get_project_folder(project.name,
                                                                                     str(op_id)),
                                                   'archive_path_prefix': str(op_id) + os.sep,
                                                   'exclude': folders_to_exclude})
                    considered_op_ids.append(op_id)

        else:
            folders_to_exclude.append("TEMP")
            to_be_exported_folders.append({'folder': project_folder,
                                           'archive_path_prefix': '', 'exclude': folders_to_exclude})

        # Compute path and name of the zip file
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d_%H-%M")
        zip_file_name = "%s_%s.%s" % (date_str, project.name, self.ZIP_FILE_EXTENSION)

        export_folder = self.build_data_export_folder(project, export_folder)
        result_path = os.path.join(export_folder, zip_file_name)

        self.initialize_tvb_zip(result_path, "w")
        # Pack project [filtered] content into a ZIP file:
        self.logger.debug("Done preparing, now we will write folders " + str(len(to_be_exported_folders)))
        self.logger.debug(str(to_be_exported_folders))
        for pack in to_be_exported_folders:
            self.write_zip_folder(**pack)
        self.logger.debug("Done exporting files, now we will export linked DTs")

        if linked_paths is not None:
            self.export_datatypes(linked_paths, op)

        # Make sure the Project.xml file gets copied:
        if optimize_size:
            self.logger.debug("Done linked, now we write the project xml")
            self.write_zip_arc(self.get_project_meta_file_path(project.name),
                               self.TVB_PROJECT_FILE)
        self.logger.debug("Done, closing")
        self.close_tvb_zip()

        return result_path

    # Generic methods start here

    def get_h5_by_gid(self, project_name, op_id, dt_gid):
        op_path = self.files_helper.get_operation_folder(project_name, op_id)

        for f in os.listdir(op_path):
            fp = os.path.join(op_path, f)
            if dt_gid in f and os.path.isfile(fp):
                return fp

    def ends_with_tvb_file_extension(self, file):
        return file.endswith(self.TVB_FILE_EXTENSION)

    def ends_with_tvb_storage_file_extension(self, file):
        return file.endswith(self.TVB_STORAGE_FILE_EXTENSION)

    def rename_project(self, current_proj_name, new_name):
        project_folder = self.get_project_folder(current_proj_name)
        if self.encryption_enabled() and not self.is_in_usage(project_folder):
            raise RenameWhileSyncEncryptingException(
                "A project can not be renamed while sync encryption operations are running")
        self.rename_project_structure(current_proj_name, new_name)
        encrypted_path = self.compute_encrypted_folder_path(project_folder)
        if os.path.exists(encrypted_path):
            new_encrypted_path = self.compute_encrypted_folder_path(
                self.get_project_folder(new_name))
            os.rename(encrypted_path, new_encrypted_path)

    def remove_project(self, project):
        project_folder = self.get_project_folder(project.name)
        self.remove_project_structure(project.name)
        encrypted_path = self.compute_encrypted_folder_path(project_folder)
        if os.path.exists(encrypted_path):
            self.remove_folder(encrypted_path)
        if os.path.exists(self.project_key_path(project.id)):
            os.remove(self.project_key_path(project.id))

    def move_datatype_with_sync(self, to_project, to_project_path, new_op_id, full_path, vm_full_path):
        self.set_project_active(to_project)
        self.sync_folders(to_project_path)

        self.move_datatype(to_project.name, str(new_op_id), full_path)
        self.move_datatype(to_project.name, str(new_op_id), vm_full_path)

        self.sync_folders(to_project_path)
        self.set_project_inactive(to_project)
