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

from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.core.entities.file.files_helper import FilesHelper
from tvb.core.neotraits.h5 import ViewModelH5
from tvb.core.services.exceptions import ProjectServiceException
from tvb.core.services.flow_service import FlowService
from tvb.core.services.operation_service import OperationService
from tvb.core.services.project_service import ProjectService
from tvb.core.services.user_service import UserService
from tvb.interfaces.rest.server.dto.dtos import DataTypeDto
from tvb.interfaces.rest.server.resources.exceptions import InvalidIdentifierException
from tvb.interfaces.rest.server.resources.project.project_resource import INVALID_PROJECT_GID_MESSAGE
from tvb.interfaces.rest.server.resources.rest_resource import RestResource
from tvb.interfaces.rest.server.resources.util import save_temporary_file

INVALID_OPERATION_GID_MESSAGE = "No operation found for GID: %s"


class GetOperationStatusResource(RestResource):
    """
    :return status of an operation
    """

    def get(self, operation_gid):
        operation = ProjectService.load_operation_by_gid(operation_gid)
        if operation is None:
            raise InvalidIdentifierException(INVALID_OPERATION_GID_MESSAGE % operation_gid)

        return {"status": operation.status}


class GetOperationResultsResource(RestResource):
    """
    :return list of DataType instances (subclasses), representing the results of that operation if it has finished and
    None, if the operation is still running, has failed or simply has no results.
    """

    def get(self, operation_gid):
        operation = ProjectService.load_operation_lazy_by_gid(operation_gid)
        if operation is None:
            raise InvalidIdentifierException(INVALID_OPERATION_GID_MESSAGE % operation_gid)

        data_types = ProjectService.get_results_for_operation(operation.id)
        if data_types is None:
            return []

        return [DataTypeDto(datatype) for datatype in data_types]


class LaunchOperationResource(RestResource):
    """ A generic method of launching Analyzers  """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operation_service = OperationService()
        self.project_service = ProjectService()
        self.user_service = UserService()
        self.files_helper = FilesHelper()

    def post(self, project_gid, algorithm_module, algorithm_classname):
        # TODO: inform user about operation gid for later monitoring
        file = self.extract_file_from_request()
        h5_path = save_temporary_file(file)

        try:
            project = self.project_service.find_project_lazy_by_gid(project_gid)
        except ProjectServiceException:
            raise InvalidIdentifierException(INVALID_PROJECT_GID_MESSAGE % project_gid)

        algorithm = FlowService.get_algorithm_by_module_and_class(algorithm_module, algorithm_classname)
        if algorithm is None:
            raise InvalidIdentifierException('No algorithm found for: %s.%s' % (algorithm_module, algorithm_classname))

        # Prepare and fire operation
        adapter_instance = ABCAdapter.build_adapter(algorithm)
        view_model = adapter_instance.get_view_model_class()()
        view_model_h5 = ViewModelH5(h5_path, view_model)
        view_model_h5.load_into(view_model)
        # TODO: use logged user
        self.flow_service.fire_operation(adapter_instance, self.user_service.get_user_by_id(1), project.id,
                                         view_model=view_model)
