from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from compas_fea2.backends._base.model import ConstraintBase
from compas_fea2.backends._base.model import TieConstraintBase


# Author(s): Francesco Ranaudo (github.com/franaudo)

__all__ = [
    'Constraint',
    'NodeTieConstraint',
]


class Constraint(ConstraintBase):
    def __init__(self, name):
        super(Constraint).__init__(name)
        raise NotImplementedError


class NodeTieConstraint(TieConstraintBase):
    def __init__(self, name, master, slave):
        super(NodeTieConstraint, self).__init__(name, master, slave, tol=None)

    def _generate_jobdata(self):

        return ''.join([
            f'** Constraint: {self.name}\n',
            '*MPC\n',
            f'TIE, {self.slave}, {self.master}\n'
        ])
