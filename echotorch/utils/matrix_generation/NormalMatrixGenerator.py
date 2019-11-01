# -*- coding: utf-8 -*-
#
# File : echotorch/utils/matrix_generation/NormalMatrixGenerator.py
# Description : Generate matrix it normally distributed weights.
# Date : 29th of October, 2019
#
# This file is part of EchoTorch.  EchoTorch is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Nils Schaetti <nils.schaetti@unine.ch>

# Import
import torch
from .MatrixGenerator import MatrixGenerator
from .MatrixFactory import matrix_factory


# Generate matrix it normally distributed weights.
class NormalMatrixGenerator(MatrixGenerator):
    """
    Generate matrix it normally distributed weights.
    """

    # Generate the matrix
    def generate(self, size, dtype=torch.float32):
        """
        Generate the matrix
        :param: Matrix size (row, column)
        :param: Data type to generate
        :return: Generated matrix
        """
        # Params
        try:
            connectivity = self._parameters['connectivity']
            mean = self._parameters['mean']
            std = self._parameters['std']
        except KeyError as k:
            raise Exception("Argument missing : {}".format(k))
        # end try

        # Full connectivity if none
        if connectivity is None:
            w = torch.zeros(size, dtype=dtype)
            w = w.normal_(mean=mean, std=std)
        else:
            w = torch.zeros(size, dtype=dtype)
            w = w.normal_(mean=mean, std=std)
            mask = torch.zeros(size, dtype=dtype)
            mask.bernoulli_(p=connectivity)
            w *= mask
        # end if
        return w
    # end generate

# end NormalMatrixGenerator


# Add
matrix_factory.register_generator("normal", NormalMatrixGenerator)
