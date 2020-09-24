#!/usr/bin/env python3

# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>. For any questions
# about this software or licensing, please email opensource@seagate.com or
# cortx-questions@seagate.com.


"""
**************************************************************************
 Description:       Cluster Management
****************************************************************************
"""

import time

from cortx.utils.log import Log
from cortx.utils.process import SimpleProcess

class Cluster:
    def __init__(self):
        """
        Manage cluster operation
        """
        pass

    def _run_cmd(self, cmd):
        """
        Run command and throw error if cmd failed
        """
        try:
            _err = ""
            _proc = SimpleProcess(cmd)
            _output, _err, _rc = _proc.run(universal_newlines=True)
            Log.debug(f"cmd: {cmd}, output: {_output}, err: {_err}, rc: {_rc}")
            if _rc != 0:
                Log.error(f"cmd: {cmd}, output: {_output}, err: {_err}, rc: {_rc}")
                raise Exception(f"Failed to execute {cmd}")
            return _output, _err, _rc
        except Exception as e:
            Log.error("Failed to execute  %s Error: %s %s" %(cmd,e,_err))
            raise Exception("Failed to execute %s Error: %s %s" %(cmd,e,_err))

    def node_status(self, node):
        pass

    def remove_node(self, node):
        pass

    def add_node(self, node):
        pass

class PcsCluster(Cluster):
    def __init__(self):
        """
        PcsCluster manage pacemaker/corosync cluster
        """
        super(PcsCluster, self).__init__()
        self._node_status = [ 'Online', 'Standby', 'Maintenance', 'Offline', 'Disconnected']

    def node_status(self, node):
        """
        Check node status
        If node not detected return rc as 1 else 0
        Node status:
         Online:
         Standby:
         Maintenance:
         Offline:
        """
        Log.debug(f"Check {node} node status")
        # TODO: check is node is valid
        _output, _err, _rc = self._run_cmd("pcs status nodes")
        for status in _output.split("\n"):
            if node in status.split():
                node_rc = 0
                node_status = (status.split()[0])[:-1]
                Log.debug(f"For {node} node rc: {node_rc}, status: {node_status}")
                return node_rc, node_status
        Log.debug(f"{node} is not detected in cluster, treating as disconnected node")
        return 1, "Disconnected"

    def remove_node(self, node):
        """
        Remove node from pcs cluster
        """
        # TODO: Limitation for node remove (in cluster node cannot remove it self)
        # Check if node already removed
        _rc, status = self.node_status(node)
        if _rc != 1:
            self._run_cmd(f"pcs cluster node remove {node} --force")
            _rc, status = self.node_status(node)
            Log.debug(f"For node {node} status: {status}, rc: {_rc}")
            if _rc != 1:
                Log.error(f"Failed to remove {node}")
                raise Exception(f"Failed to remove {node}")
            else:
                Log.info(f"Node {node} removed from cluster")
        else:
            Log.info(f"Node {node} already removed from cluster")

    def add_node(self, node):
        """
        Add new node to pcs cluster
        """
        # TODO: Limitation for node add (in cluster node cannot add it self)
        commands = [f"pcs cluster node add {node}",
                "pcs resource cleanup --all",
                f"pcs cluster enable {node}",
                f"pcs cluster start {node}"]
        _rc, status = self.node_status(node)
        if _rc != 0:
            for command in commands:
                self._run_cmd(command)
            time.sleep(20)
            _rc, status = self.node_status(node)
            Log.debug(f"{node} status rc: {_rc}, status: {status}")
            if status != 'Online':
                Log.error(f"Failed to add {node}")
                raise Exception(f"Failed to add {node}")
            else:
                Log.info(f"Node {node} added to cluster")
        else:
            Log.info(f"Node {node} already added to cluster")