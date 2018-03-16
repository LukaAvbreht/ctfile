#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

from __future__ import print_function, division, unicode_literals
import sys
import json
import io
from collections import OrderedDict
from collections import UserList

from .utils import OrderedCounter
from .utils import ctab_properties_conf

class CTfile(object):
    """Base class to represent collection of Chemical table file (``CTfile``) formats, e.g. ``Molfile``, ``SDfile``."""
    ctab_properties = ctab_properties_conf

    def __init__(self, lexer):
        """CTfile initializer.
        
        :param lexer: instance of the ``CTfile`` format tokenizer.
        :type lexer: :func:`~ctfile.tokenizer.tokenizer`
        """
        self.lexer = lexer
        self._build()

    def read(self, filehandle):
        """

        :param filehandle:
        :return:
        """
        input_str = filehandle.read()

    def write(self, filehandle, file_format):
        """Write :class:`~ctfile.ctfile.CTfile` data into file. 

        :param filehandle: File-like object.
        :param str file_format: Format to use to write data: ``ctfile`` or ``json``.
        :return: None.
        :rtype: :py:obj:`None`
        """
        try:
            filehandle.write(self.writestr(file_format=file_format))
        except IOError:
            raise IOError('"filehandle" parameter must be writable.')

    def writestr(self, file_format):
        """Write :class:`~ctfile.ctfile.CTfile` data into string.
        
        :param str file_format: Format to use to write data: ``ctfile`` or ``json``.
        :return: String representing the :class:`~ctfile.ctfile.CTfile` instance.
        :rtype: :py:class:`str`
        """
        if file_format == 'json':
            repr_str = self._to_json()
        elif file_format == 'ctfile':
            repr_str = self._to_ctfile()
        else:
            raise ValueError('Invalid "file_format" argument: "{}"'.format(file_format))
        return repr_str

    def print_file(self, file_format='ctfile', f=sys.stdout):
        """Print representation of :class:`~ctfile.ctfile.CTfile`.

        :param str file_format: Format to use: ``ctfile`` or ``json``.
        :param f: Print to file or stdout.
        :type f: File-like 
        :return: None.
        :rtype: :py:obj:`None`
        """
        print(self.writestr(file_format=file_format), file=f)

    def _build(self):
        """Build :class:`~ctfile.ctfile.CTfile` instance.

        :return: :class:`~ctfile.ctfile.CTfile` instance.
        :rtype: :class:`~ctfile.ctfile.CTfile`
        """
        raise NotImplementedError('Subclass must implement abstract method')

    def _to_json(self, sort_keys=False, indent=4):
        """Convert :class:`~ctfile.ctfile.CTfile` into JSON string.
        
        :return: ``JSON`` formatted string.
        :rtype: :py:class:`str`
        """
        return json.dumps(self, sort_keys=sort_keys, indent=indent)

    def _to_ctfile(self):
        """Convert :class:`~ctfile.ctfile.CTfile` into `CTfile` formatted string.
        
        :return: ``CTfile`` formatted string.
        :rtype: :py:class:`str`
        """
        raise NotImplementedError('Subclass must implement abstract method')

    @staticmethod
    def _is_molfile(string):
        """Test if input string is in ``Molfile`` format.

        :param string: Input string.
        :type string: :py:class:`str` or :py:class:`bytes`
        :return: Input string if in ``Molfile`` format or False otherwise.
        :rtype: :py:class:`str` or :py:obj:`False`
        """
        pass

    @staticmethod
    def _is_sdfile(string):
        """Test if input string is in ``SDfile`` format.

        :param string: Input string.
        :type string: :py:class:`str` or :py:class:`bytes`
        :return: Input string if in ``SDfile`` format or False otherwise.
        :rtype: :py:class:`str` or :py:obj:`False`
        """
        pass


class Ctab(CTfile, OrderedDict):
    """Ctab - connection table contains information describing the structural relationships
    and properties of a collection of atoms.
    
    --------------------
    | CTab             |
    |                  |
    | Counts line      |
    | Atom block       |
    | Bond block       |
    | Properties block |
    |                  |
    --------------------
    
    * Counts line: specifies the number of atoms, bonds, Sgroups, 3D constituents, as well as
      the chiral flag setting, and the regno.
    * Atom block: specifies an atomic symbol and any mass difference, charge, stereochemistry,
      and associated hydrogens for each atom.
    * Bond block: Specifies the two atoms connected by the bond, the bond type, and any bond
      stereochemistry and topology (chain or ring properties) for each bond.
    * Properties block: specifies additional properties.
    
    counts line format: aaabbblllfffcccsssxxxrrrpppiiimmmvvvvvv
    where:
        aaa = number of atoms
        bbb = number of bonds
        lll = number of atom lists
        fff = (obsolete)
        ccc = chiral flag: 0=not chiral, 1=chiral
        sss = number of stext entries
        xxx = (obsolete)
        rrr = (obsolete)
        ppp = (obsolete)
        iii = (obsolete)
        mmm = number of lines of additional properties
    
    atom block format: xxxxxxxxxxyyyyyyyyyyzzzzzzzzzzaaaaddcccssshhhbbbvvvHHHrrriiimmmnnneee
    where:
        xxxxxxxxxx = atom x coordinate
        yyyyyyyyyy = atom y coordinate
        zzzzzzzzzz = atom z coordinate
        aaa        = atom symbol
        dd         = mass difference: -3, -2, -1, 0, 1, 2, 3, 4, (0 if value beyond these limits)
        ccc        = charge: 0=uncharged or value other than these, 1=+3, 2=+2, 3=+1, 
                     4=doublet radical, 5=-1, 6=-2, 7=-3
        sss        = atom stereo parity: 0=not stereo, 1=odd, 2=even, 3=either or unmarked stereo center
        hhh        = hydrogen count + 1: 1=H0, 2=H1, 3=H2, 4=H3, 5=H4
        bbb        = stereo care box: 0=ignore stereo configuration of this double bond atom, 
                     1=stereo configuration of double bond atom must match
        vvv        = valence: 0=no marking (default), (1 to 14)=(1 to 14), 15=zero valence
        HHH        = H0 designator: 0=not specified, 1=no H atoms allowed
        rrr        = (obsolete)
        iii        = (obsolete)
        mmm        = atom-atom mapping number: 1=number of atoms
        nnn        = inversion/retention flag: 0=property not applied 1=configuration is inverted, 
                     2=configuration is retained
        eee        = exact change flag: 0=property not applied, 1=change on atom must be exactly as shown
    
    bond block format: 111222tttsssxxxrrrccc
    where:
        111 = first atom number: 1=number of atoms
        222 = second atom number: 1=number of atoms
        ttt = bond type: 1=Single, 2=Double, 3=Triple, 4=Aromatic, 5=Single or Double, 6=Single or Aromatic, 
              7=Double or Aromatic, 8=Any
        sss = bond stereo: Single bonds: 0=not stereo, 1=Up, 4=Either, 6=Down; 
              Double bonds: 0=Use x-, y-, z-coords from atom block to determine cis or trans, 
              3=Cis or trans (either) double bond
        xxx = (obsolete)
        rrr = bond topology: 0=Either, 1=Ring, 2=Chain
        ccc = reacting center status: 0=unmarked, 1=a center, -1=not a center; 
              Additional: 2=no change, 4=bond made/broken, 8=bond order changes 12=4+8 (both made/broken and changes); 
              5=(4 + 1), 9=(8 + 1), and 13=(12 + 1) are also possible
    
    properties block: 
    where:
        Most lines in the properties block are identified by a prefix of the form "M  XXX" where two spaces 
        separate the M and XXX.
        The prefix: "M  END" terminates the properties block.
    """
    counts_line_format = 'aaabbblllfffcccsssxxxrrrpppiiimmmvvvvvv'
    atom_block_format = 'xxxxxxxxxxyyyyyyyyyyzzzzzzzzzzaaaaddcccssshhhbbbvvvHHHrrriiimmmnnneee'
    bond_block_format = '111222tttsssxxxrrrccc'

    def __init__(self, lexer):
        """Ctab initializer.
        
        :param lexer: 
        """
        self["CtabCountsLine"] = OrderedDict()
        self["CtabAtomBlock"] = []
        self["CtabBondBlock"] = []
        self["CtabPropertiesBlock"] = OrderedDict()
        super(Ctab, self).__init__(lexer)

    def _build(self):
        """Build :class:`~ctfile.ctfile.Ctab` instance.
        
        :return: :class:`~ctfile.ctfile.Ctab` instance.
        :rtype: :class:`~ctfile.ctfile.Ctab`
        """
        for token in self.lexer:
            key = token.__class__.__name__

            if key == 'CtabCountsLine':
                self[key].update(token._asdict())

            elif key in ('CtabAtomBlock', 'CtabBondBlock'):
                self[key].append(token._asdict())

            elif key == 'CtabPropertiesBlock':
                self[key].setdefault(token.name, []).append(token.line)

            else:
                raise KeyError('Ctab object does not supposed to have any other information: "{}".'.format(key))

    def _to_ctfile(self):
        """Convert :class:`~ctfile.ctfile.CTfile` into `CTfile` formatted string.

        :return: `CTfile` formatted string.
        :rtype: :py:class:`str`
        """
        output = io.StringIO()

        for key in self:

            if key == 'CtabCountsLine':
                counter = OrderedCounter(self.counts_line_format)
                counts_line = ''.join([str(value).rjust(spacing) for value, spacing
                                       in zip(self[key].values(), counter.values())])
                output.write(counts_line)
                output.write('\n')

            elif key == 'CtabAtomBlock':
                counter = OrderedCounter(self.atom_block_format)

                for i in self[key]:
                    atom_line = ''.join([str(value).rjust(spacing) for value, spacing
                                         in zip(i.values(), counter.values())])
                    output.write(atom_line)
                    output.write('\n')

            elif key == 'CtabBondBlock':
                counter = OrderedCounter(self.bond_block_format)

                for i in self[key]:
                    bond_line = ''.join([str(value).rjust(spacing) for value, spacing
                                         in zip(i.values(), counter.values())])
                    output.write(bond_line)
                    output.write('\n')

            elif key == 'CtabPropertiesBlock':
                for property_name in self[key]:
                    for property_line in self[key][property_name]:
                        output.write(property_line)
                        output.write('\n')
                output.write(self.ctab_properties[self.version]['END']['fmt'])

            else:
                raise KeyError('Ctab object does not supposed to have any other information: "{}".'.format(key))

        return output.getvalue()

    @property
    def version(self):
        """Version of the `CTfile` formatting.
        
        :return: Version of the `CTfile`.
        :rtype: str
        """
        return self['CtabCountsLine']['version']

    @property
    def atoms(self):
        """List of atoms.

        :return: List of atoms.
        :rtype: :py:class:`list`
        """
        return [atom_line['atom_symbol'] for atom_line in self['CtabAtomBlock']]

    @property
    def positions(self):
        """List of positions of atoms in atoms block starting from 1.
        
        :return: List of positions of atoms in atoms block starting from 1. 
        :rtype: :py:class:`list`
        """
        return [str(i) for i in range(1, len(self.atoms)+1)]

    @property
    def iso(self, property_specifier='ISO'):
        """

        :return:
        """
        isotopes = []

        if property_specifier in self['CtabPropertiesBlock']:
            position_atom = dict(zip(self.positions, self.atoms))

            for property_line in self['CtabPropertiesBlock'][property_specifier]:
                property_values = property_line.split()[3:]
                property_values_per_atom = [property_values[i:i+2] for i in range(0, len(property_values), 2)]

                for entry in property_values_per_atom:
                    position, isotope = entry
                    atom_symbol = position_atom[position]
                    isotopes.append({"atom_symbol": atom_symbol, "isotope": isotope, "position": position})

        return isotopes


class Molfile(CTfile, OrderedDict):
    """Molfile - each molfile describes a single molecular structure which can
    contain disjoint fragments.
    
    --------------------
    | molfile          |
    |                  |
    |                  |
    |   ---------      |
    |   | Ctab  |      |
    |   ---------      |
    |                  |
    --------------------
    """
    def __init__(self, lexer):
        """Molfile initializer.
        
        :param lexer: 
        """
        self["HeaderBlock"] = OrderedDict()
        self["Ctab"] = OrderedDict()
        super(Molfile, self).__init__(lexer)

    def _build(self):
        """Build :class:`~ctfile.ctfile.Molfile` instance.

        :return: :class:`~ctfile.ctfile.Molfile` instance.
        :rtype: :class:`~ctfile.ctfile.Molfile`
        """
        for token in self.lexer:
            key = token.__class__.__name__

            if key == 'HeaderBlock':
                self[key].update(token._asdict())

            elif key == 'CtabBlock':
                ctab = Ctab(lexer=self.lexer)
                self['Ctab'] = ctab

            else:
                raise KeyError('Molfile object does not supposed to have any other information: "{}".'.format(key))

        return self

    def _to_ctfile(self):
        """Convert :class:`~ctfile.ctfile.CTfile` into `CTfile` formatted string.

        :return: ``CTfile`` formatted string.
        :rtype: :py:class:`str`
        """
        output = io.StringIO()

        for key in self:
            if key == 'HeaderBlock':
                for line in self[key].values():
                    output.write(line)
                    output.write('\n')

            elif key == 'Ctab':
                ctab_str = self[key]._to_ctfile()
                output.write(ctab_str)

            else:
                raise KeyError('Molfile object does not supposed to have any other information: "{}".'.format(key))

        return output.getvalue()

    @property
    def version(self):
        """Version of the `CTfile` formatting.

        :return: Version of the `CTfile`.
        :rtype: str
        """
        return self['Ctab'].version

    @property
    def atoms(self):
        """List of atoms.

        :return: List of atoms.
        :rtype: :py:class:`list`
        """
        return self['Ctab'].atoms

    @property
    def positions(self):
        """List of positions of atoms in atoms block starting from 1.
        
        :return: List of positions of atoms in atoms block starting from 1. 
        :rtype: :py:class:`list`
        """
        return self['Ctab'].positions

    @property
    def iso(self):
        return self['Ctab'].iso


class SDfile(CTfile, UserList):
    """SDfile - each structure-data file contains structures and data for any number
    of molecules.

    ---------------------
    | SDfile       .    |
    |            .      |
    |          .        |
    | ----------------- |
    | | ------------- | |
    | | | molfile   | | |
    | | | or RGfile | | |
    | | ------------- | |
    | | ------------- | |
    | | | data      | | |
    | | | block     | | |
    | | ------------- | |
    | ----------------- |
    ---------------------
    """
    pass