# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2022, Baycrest Centre for Geriatric Care ("Baycrest") and others
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

import os
import pytest
import tvb_data

from tvb.adapters.datatypes.db.connectivity import ConnectivityIndex
from tvb.core.utils import no_matlab
from tvb.interfaces.rest.commons.exceptions import InvalidIdentifierException
from tvb.interfaces.rest.server.resources.datatype.datatype_resource import RetrieveDatatypeResource, \
    GetOperationsForDatatypeResource
from tvb.interfaces.rest.server.resources.project.project_resource import GetDataInProjectResource
from tvb.storage.storage_interface import StorageInterface
from tvb.tests.framework.core.factory import TestFactory
from tvb.tests.framework.interfaces.rest.base_resource_test import RestResourceTest


class TestDatatypeResource(RestResourceTest):

    def transactional_setup_method(self):
        self.test_user = TestFactory.create_user('Rest_User')
        self.test_project = TestFactory.create_project(self.test_user, 'Rest_Project', users=[self.test_user.id])
        self.retrieve_resource = RetrieveDatatypeResource()
        self.get_operations_resource = GetOperationsForDatatypeResource()
        self.get_data_in_project_resource = GetDataInProjectResource()

    def test_server_retrieve_datatype_inexistent_gid(self, mocker):
        self._mock_user(mocker)
        datatype_gid = "inexistent-gid"
        with pytest.raises(InvalidIdentifierException): self.retrieve_resource.get(datatype_gid=datatype_gid)

    def test_server_retrieve_datatype(self, mocker):
        self._mock_user(mocker)
        zip_path = os.path.join(os.path.dirname(tvb_data.__file__), 'connectivity', 'connectivity_96.zip')
        TestFactory.import_zip_connectivity(self.test_user, self.test_project, zip_path)

        datatypes_in_project = self.get_data_in_project_resource.get(project_gid=self.test_project.gid)
        assert type(datatypes_in_project) is list
        assert len(datatypes_in_project) == 1
        assert datatypes_in_project[0].type == ConnectivityIndex().display_type

        def send_file_dummy(path, as_attachment, attachment_filename):
            return (path, as_attachment, attachment_filename)

        # Mock flask.send_file to behave like send_file_dummy
        mocker.patch('flask.send_file', send_file_dummy)
        result = self.retrieve_resource.get(datatype_gid=datatypes_in_project[0].gid)

        assert type(result) is tuple
        assert result[1] is True
        assert os.path.basename(result[0]) == os.path.basename(result[2])

    @pytest.mark.skipif(no_matlab(), reason="Matlab or Octave not installed!")
    def test_server_get_operations_for_datatype(self, mocker):
        self._mock_user(mocker)
        zip_path = os.path.join(os.path.dirname(tvb_data.__file__), 'connectivity', 'connectivity_96.zip')
        TestFactory.import_zip_connectivity(self.test_user, self.test_project, zip_path)

        datatypes_in_project = self.get_data_in_project_resource.get(project_gid=self.test_project.gid)
        assert type(datatypes_in_project) is list
        assert len(datatypes_in_project) == 1
        assert datatypes_in_project[0].type == ConnectivityIndex().display_type

        result = self.get_operations_resource.get(datatype_gid=datatypes_in_project[0].gid)
        assert type(result) is list
        assert len(result) > 3

    def transactional_teardown_method(self):
        StorageInterface().remove_project_structure(self.test_project.name)
