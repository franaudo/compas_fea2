from compas_fea2.backends._base.base import FEABase


class ContactPairBase(FEABase):
    """Pair of master and slave surfaces to assign an interaction property

    Parameters
    ----------
    FEABase : [type]
        [description]
    """

    def __init__(self, name, master, slave, interaction):
        self._name = name
        self._master = master
        self._slave = slave
        self._interaction = interaction

    @property
    def name(self):
        """str : the name of the contact pair."""
        return self._name

    @property
    def master(self):
        """obj : type :class:`SurfaceBase` object to be used as master."""
        return self._master

    @property
    def slave(self):
        """obj : type :class:`SurfaceBase` object to be used as slave."""
        return self._slave

    @property
    def interaction(self):
        """str : name of a previusly defined :class:`InterfaceBase` object to
        define the type of interaction between master and slave."""
        return self._interaction
