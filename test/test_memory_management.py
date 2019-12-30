# -*- coding: utf-8 -*-
#
# File : test/test_memory_management.py
# Description : Test incremental reservoir loading and output learning, quota and generation.
# Date : 18th of December, 2019
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

# Imports
import os
import echotorch.utils
from .EchoTorchTestCase import EchoTorchTestCase
import numpy as np
import torch
import echotorch.nn.conceptors as ecnc
import echotorch.utils.matrix_generation as mg
import echotorch.utils
import echotorch.datasets as etds
from echotorch.datasets import DatasetComposer
from echotorch.nn.Node import Node
from torch.utils.data.dataloader import DataLoader
from torch.autograd import Variable


# Test case : incremental loading and memory management
class Test_Memory_Management(EchoTorchTestCase):
    """
    Incremental loading and memory management
    """
    # region BODY

    # region PUBLIC

    # Memory management
    def memory_management(self, data_dir, expected_NRMSEs, reservoir_size=100, spectral_radius=1.5, input_scaling=1.5,
                          bias_scaling=0.25, connectivity=10.0, washout_length=100, learn_length=100,
                          ridge_param_wout=0.01, aperture=1000, precision=0.001,
                          torch_seed=1, np_seed=1, interpolation_rate=20, conceptor_test_length=200,
                          signal_plot_length=20, loading_method=ecnc.SPESNCell.INPUTS_SIMULATION,
                          use_matlab_params=True):
        """
        Memory management
        """
        # Package
        subpackage_dir, this_filename = os.path.split(__file__)
        package_dir = os.path.join(subpackage_dir, "..")
        TEST_PATH = os.path.join(package_dir, "data", "tests", data_dir)

        # Debug
        debug_mode = Node.DEBUG_TEST_CASE

        # Random numb. init
        torch.random.manual_seed(torch_seed)
        np.random.seed(np_seed)

        # Precision decimal
        precision_decimals = int(-np.log10(precision))

        # Type params
        dtype = torch.float64

        # Reservoir parameters
        connectivity = connectivity / reservoir_size

        # Pattern parameters
        n_patterns = 16

        # 2. We generate matrices Wstar, Win and Wbias,
        # either from a random number generator or from
        # matlab files.

        # Load W from matlab file and random init ?
        if use_matlab_params:
            # Load internal weights
            w_generator = mg.matrix_factory.get_generator(
                "matlab",
                file_name=os.path.join(TEST_PATH, "WRaw.mat"),
                entity_name="WRaw",
                scale=spectral_radius
            )

            # Load internal weights
            win_generator = mg.matrix_factory.get_generator(
                "matlab",
                file_name=os.path.join(TEST_PATH, "WinRaw.mat"),
                entity_name="WinRaw",
                scale=input_scaling
            )

            # Load Wbias from matlab from or init randomly
            wbias_generator = mg.matrix_factory.get_generator(
                "matlab",
                file_name=os.path.join(TEST_PATH, "WbiasRaw.mat"),
                entity_name="WbiasRaw",
                shape=reservoir_size,
                scale=bias_scaling
            )
        else:
            # Generate internal weights
            w_generator = mg.matrix_factory.get_generator(
                "normal",
                mean=0.0,
                std=1.0,
                connectivity=connectivity,
                spectral_radius=spectral_radius
            )

            # Generate Win
            win_generator = mg.matrix_factory.get_generator(
                "normal",
                mean=0.0,
                std=1.0,
                connectivity=1.0,
                scale=input_scaling
            )

            # Load Wbias from matlab from or init randomly
            wbias_generator = mg.matrix_factory.get_generator(
                "normal",
                mean=0.0,
                std=1.0,
                connectivity=1.0,
                scale=bias_scaling
            )
        # end if

        # 3. We create the different patterns to be loaded
        # into the reservoir and learned by the Conceptors.
        # There is 13 patterns, 3 are repeated (6, 7, 8)
        # to show that it does not increase memory size.

        # Pattern 1 (sine p=10)
        pattern1_training = etds.SinusoidalTimeseries(
            sample_len=washout_length + learn_length,
            n_samples=1,
            a=1,
            period=10,
            dtype=dtype
        )

        # Pattern 2 (sine p=15)
        pattern2_training = etds.SinusoidalTimeseries(
            sample_len=washout_length + learn_length,
            n_samples=1,
            a=1,
            period=15,
            dtype=dtype
        )

        # Pattern 3 (periodic 4)
        pattern3_training = etds.PeriodicSignalDataset(
            sample_len=washout_length + learn_length,
            n_samples=1,
            period=[-0.4564, 0.6712, -2.3953, -2.1594],
            dtype=dtype
        )

        # Pattern 4 (periodic 6)
        pattern4_training = etds.PeriodicSignalDataset(
            sample_len=washout_length + learn_length,
            n_samples=1,
            period=[0.5329, 0.9621, 0.1845, 0.5099, 0.3438, 0.7697],
            dtype=dtype
        )

        # Pattern 5 (periodic 7)
        pattern5_training = etds.PeriodicSignalDataset(
            sample_len=washout_length + learn_length,
            n_samples=1,
            period=[0.8029, 0.4246, 0.2041, 0.0671, 0.1986, 0.2724, 0.5988],
            dtype=dtype
        )

        # Pattern 6 (sine p=12)
        pattern6_training = etds.SinusoidalTimeseries(
            sample_len=washout_length + learn_length,
            n_samples=1,
            a=1,
            period=12,
            dtype=dtype
        )

        # Pattern 7 (sine p=5)
        pattern7_training = etds.SinusoidalTimeseries(
            sample_len=washout_length + learn_length,
            n_samples=1,
            a=1,
            period=5,
            dtype=dtype
        )

        # Pattern 8 (sine p=6)
        pattern8_training = etds.SinusoidalTimeseries(
            sample_len=washout_length + learn_length,
            n_samples=1,
            a=1,
            period=6,
            dtype=dtype
        )

        # Pattern 9 (periodic 8)
        pattern9_training = etds.PeriodicSignalDataset(
            sample_len=washout_length + learn_length,
            n_samples=1,
            period=[0.8731, 0.1282, 0.9582, 0.6832, 0.7420, 0.9829, 0.4161, 0.5316],
            dtype=dtype
        )

        # Pattern 10 (periodic 7)
        pattern10_training = etds.PeriodicSignalDataset(
            sample_len=washout_length + learn_length,
            n_samples=1,
            period=[0.6792, 0.5129, 0.2991, 0.1054, 0.2849, 0.7689, 0.6408],
            dtype=dtype
        )

        # Pattern 11 (periodic 3)
        pattern11_training = etds.PeriodicSignalDataset(
            sample_len=washout_length + learn_length,
            n_samples=1,
            period=[1.4101, -0.0992, -0.0902],
            dtype=dtype
        )

        # Pattern 12 (sine p=6)
        pattern12_training = etds.SinusoidalTimeseries(
            sample_len=washout_length + learn_length,
            n_samples=1,
            a=1,
            period=11,
            dtype=dtype
        )

        # Pattern 13 (periodic 5)
        pattern13_training = etds.PeriodicSignalDataset(
            sample_len=washout_length + learn_length,
            n_samples=1,
            period=[0.9, -0.021439412841318672, 0.0379515995051003, -0.9, 0.06663989939293802],
            dtype=dtype
        )

        # Composer
        dataset_training = DatasetComposer([
            pattern1_training, pattern2_training, pattern3_training, pattern4_training, pattern5_training,
            pattern1_training,
            pattern2_training, pattern3_training, pattern6_training, pattern7_training, pattern8_training,
            pattern9_training,
            pattern10_training, pattern11_training, pattern12_training, pattern13_training
        ])

        # Data loader
        patterns_loader = DataLoader(dataset_training, batch_size=1, shuffle=False, num_workers=1)

        # 4. We create a conceptor set, 16 conceptors,
        # and an incremental conceptor net (IncConceptorNet)

        # Create a set of conceptors
        conceptors = ecnc.ConceptorSet(input_dim=reservoir_size, debug=debug_mode, test_case=self)

        # Create sixteen conceptors
        for p in range(n_patterns):
            conceptors.add(
                p,
                ecnc.Conceptor(
                    input_dim=reservoir_size,
                    aperture=aperture,
                    debug=debug_mode,
                    test_case=self,
                    dtype=dtype
                )
            )
        # end for

        # Create a conceptor network using
        # an incrementing self-predicting ESN which
        # will learn sixteen patterns
        conceptor_net = ecnc.IncConceptorNet(
            input_dim=1,
            hidden_dim=reservoir_size,
            output_dim=1,
            conceptor=conceptors,
            w_generator=w_generator,
            win_generator=win_generator,
            wbias_generator=wbias_generator,
            ridge_param_wout=ridge_param_wout,
            aperture=aperture,
            washout=washout_length,
            fill_left=True,
            loading_method=loading_method,
            debug=debug_mode,
            test_case=self,
            dtype=dtype
        )

        # 6. For debugging, we add some debug point
        # which will compute the differences between
        # what we want and what we have. You will then be
        # able to check if there is a problem.

        # If with matlab info
        if use_matlab_params:
            # Load sample matrices
            for i in range(n_patterns):
                # SPESN : Input patterns
                conceptor_net.cell.debug_point(
                    "u{}".format(i),
                    torch.reshape(torch.from_numpy(np.load("data/tests/memory_management/u{}.npy".format(i))),
                                  shape=(-1, 1)),
                    precision
                )

                # SPESN : States X
                conceptor_net.cell.debug_point(
                    "X{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/X{}.npy".format(i)).T),
                    precision
                )

                # SPESN : States old
                conceptor_net.cell.debug_point(
                    "Xold{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/XOld{}.npy".format(i)).T),
                    precision
                )

                # SPESN : Td
                if loading_method != ecnc.SPESNCell.INPUTS_RECREATION:
                    conceptor_net.cell.debug_point(
                        "Td{}".format(i),
                        torch.from_numpy(np.load("data/tests/memory_management/Td{}.npy".format(i)).T),
                        precision if i < 13 else precision * 100
                    )
                # end if

                # SPESN : F
                if i != 15:
                    conceptor_net.cell.debug_point(
                        "F{}".format(i),
                        torch.from_numpy(np.load("data/tests/memory_management/F{}.npy".format(i))),
                        precision * 10
                    )
                # end if

                # SPESN : Sold
                conceptor_net.cell.debug_point(
                    "Sold{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/Sold{}.npy".format(i)).T),
                    precision if i < 15 else precision * 10
                )

                # SPESN : sTd
                if loading_method != ecnc.SPESNCell.INPUTS_RECREATION:
                    conceptor_net.cell.debug_point(
                        "sTd{}".format(i),
                        torch.from_numpy(np.load("data/tests/memory_management/sTd{}.npy".format(i))),
                        precision if i < 15 else precision * 100
                    )
                # end if

                # SPESN : sTs
                conceptor_net.cell.debug_point(
                    "sTs{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/sTs{}.npy".format(i))),
                    precision if i < 9 else precision * 10
                )

                # SPESN : ridge sTs
                conceptor_net.cell.debug_point(
                    "ridge_sTs{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/ridge_sTs{}.npy".format(i))),
                    precision
                )

                # SPESN : Dinc
                if i != 15:
                    conceptor_net.cell.debug_point(
                        "Dinc{}".format(i),
                        torch.from_numpy(np.load("data/tests/memory_management/Dinc{}.npy".format(i))),
                        precision if i < 14 else precision * 100
                    )
                # end if

                # SPESN : D
                if i != 15:
                    conceptor_net.cell.debug_point(
                        "D{}".format(i),
                        torch.from_numpy(np.load("data/tests/memory_management/D{}.npy".format(i))),
                        precision if i < 14 else precision * 100
                    )
                # end if

                # Conceptor : C matrix
                conceptors[i].debug_point(
                    "C",
                    torch.from_numpy(np.load("data/tests/memory_management/C{}.npy".format(i))),
                    precision
                )

                # IncRRCell : Wout Y
                conceptor_net.output.debug_point(
                    "Y{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/Y{}.npy".format(i)).T),
                    precision
                )

                # IncRRCell : Wout y
                conceptor_net.output.debug_point(
                    "y{}".format(i),
                    torch.reshape(torch.from_numpy(np.load("data/tests/memory_management/u{}.npy".format(i))),
                                  shape=(-1, 1)),
                    precision
                )

                # IncRRCell : Wout F
                conceptor_net.output.debug_point(
                    "F{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/Wout_F{}.npy".format(i))),
                    precision if i < 15 else precision * 10
                )

                # IncRRCell : Wout S
                conceptor_net.output.debug_point(
                    "S{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/S{}.npy".format(i)).T),
                    precision if i < 15 else precision * 10
                )

                # IncRRCell : Wout sTs
                conceptor_net.output.debug_point(
                    "sTs{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/Wout_sTs{}.npy".format(i))),
                    precision if i < 9 else precision * 10
                )

                # IncRRCell : Wout sTy
                conceptor_net.output.debug_point(
                    "sTy{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/sTy{}.npy".format(i))),
                    precision
                )

                # IncRRCell : Wout ridge sTs
                conceptor_net.output.debug_point(
                    "ridge_sTs{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/Wout_ridge_sTs{}.npy".format(i))),
                    precision
                )

                # IncRRCell : Wout inverse of ridge sTs
                if i < 9:
                    inv_sts_precision = precision
                elif i < 15:
                    inv_sts_precision = precision * 10
                else:
                    inv_sts_precision = precision * 100
                # end if

                conceptor_net.output.debug_point(
                    "inv_sTs{}".format(i),
                    torch.from_numpy(np.load("data/tests/memory_management/Wout_inv_ridge_sTs{}.npy".format(i))),
                    inv_sts_precision
                )

                # IncRRCell : Wout
                conceptor_net.output.debug_point(
                    "w_out{}".format(i),
                    torch.reshape(torch.from_numpy(np.load("data/tests/memory_management/Wout{}.npy".format(i))), shape=(1, -1)),
                    precision
                )
            # end for

            # Load test W
            conceptor_net.cell.debug_point(
                "Wstar",
                torch.from_numpy(np.load("data/tests/memory_management/Wstar.npy", allow_pickle=True)),
                precision
            )

            # Load test Win
            conceptor_net.cell.debug_point(
                "Win",
                torch.from_numpy(np.load("data/tests/memory_management/Win.npy")),
                precision
            )

            # Load test Wbias
            conceptor_net.cell.debug_point(
                "Wbias",
                torch.from_numpy(np.load("data/tests/memory_management/Wbias.npy")),
                precision
            )
        # end if

        # 7. We incrementally load the patterns into the reservoir
        # and we save the results for plotting and testing.

        # Save pattern for plotting, last state, quota after each loading
        P_collector = torch.empty(n_patterns, signal_plot_length, dtype=dtype)
        last_states = torch.empty(n_patterns, reservoir_size, dtype=dtype)
        quota_collector = torch.zeros(n_patterns)

        # Conceptors activated in the loop
        conceptor_net.conceptor_active(True)

        # For each sample in the dataset
        for p, data in enumerate(patterns_loader):
            # Inputs and labels
            inputs, outputs, labels = data

            # To Variable
            if dtype == torch.float64:
                inputs, outputs = Variable(inputs.double()), Variable(outputs.double())
            # end if

            # Set the conceptor activated in
            # the loop.
            conceptors.set(p)

            # Feed SPESN with inputs,
            # output learning to recreate the inputs
            # so the inputs are the targets.
            X = conceptor_net(inputs, inputs)

            # Finalize Conceptor by learning
            # the Conceptor matrix from the
            # neurons activation received in
            # the preceding line.
            conceptors[p].finalize()

            # We change the aperture of the Conceptor,
            # the Conceptor matrix C is modified.
            conceptors[p].aperture = aperture

            # We save the patterns to be plotted afterwards,
            # we save the last state to start the generation.
            # we also save the quota of the space used by the
            # patterns currently loaded in the reservoir.
            P_collector[p] = inputs[0, washout_length:washout_length + signal_plot_length, 0]
            last_states[p] = X[0, -1]
            quota_collector[p] = conceptors.quota()
        # end for

        # 8. We test the system by generating signals,
        # we align these with original patterns and
        # we measure its performances with NRMSE.

        # We are going to to some pattern
        # generation, so we stop the learning
        # and switch to the evaluation mode.
        conceptor_net.train(False)

        # For each pattern we generate a sample by filtering the neurons
        # activation with the selected Conceptor, we then align the
        # generated sample to the real pattern by testing different
        # phase shift and we save the result.
        for p in range(n_patterns):
            # Set the current conceptor
            # corresponding to the pth pattern.
            conceptors.set(p)

            # Set last state in training phase as initial
            # state here.
            conceptor_net.cell.set_hidden(last_states[p])

            # Generate sample, we give a zero input of size
            # batch size x time length x number of inputs.
            # We don't reset the state as we set the initial state
            # just before.
            generated_sample = conceptor_net(torch.zeros(1, conceptor_test_length, 1, dtype=dtype), reset_state=False)

            # We find the best phase shift by interpolating the original
            # and the generated signal quadratically and trying different
            # shifts. We take the best under the NRMSE evaluation measure.
            _, _, NRMSE_aligned = echotorch.utils.pattern_interpolation(
                P_collector[p],
                generated_sample[0],
                interpolation_rate
            )

            # Check NRMSE
            self.assertAlmostEqual(NRMSE_aligned, expected_NRMSEs[p], precision_decimals)
        # end for
    # end memory_management

    # endregion PUBLIC

    # region TEST

    # Memory management (input simulation) with matlab info
    def test_memory_management_matlab(self):
        """
        Memory management
        """
        # Test with matlab params
        self.memory_management(
            data_dir="memory_management",
            use_matlab_params=True,
            expected_NRMSEs=[
                0.01825501182411578,
                0.022420943203613906,
                0.0028304998508909174,
                0.02841607835076219,
                0.029260350859960222,
                0.01825501182411578,
                0.022420943203613906,
                0.0028304998508909174,
                0.1671342727324171,
                0.0051145493052900,
                0.0275242645293474,
                0.0230442825704813,
                0.0249327812343836,
                0.0059416182339191,
                0.1890864223241806,
                1.4962894916534424
            ]
        )
    # end test_memory_management_matlab

    # Memory management (input recreation) with matlab info
    def test_memory_management_input_recreation_matlab(self):
        """
        Memory management
        """
        # Test with matlab params
        self.memory_management(
            data_dir="memory_management",
            use_matlab_params=True,
            loading_method=ecnc.SPESNCell.INPUTS_RECREATION,
            expected_NRMSEs=[
                0.01825501182411578,
                0.022420943203613906,
                0.0028304998508909174,
                0.02841607835076219,
                0.029260350859960222,
                0.01825501182411578,
                0.022420943203613906,
                0.0028304998508909174,
                0.1671342727324171,
                0.0051145493052900,
                0.0275242645293474,
                0.0230442825704813,
                0.0249327812343836,
                0.0059416182339191,
                0.1890864223241806,
                1.4962894916534424
            ]
        )
    # end test_memory_management_input_recreation_matlab

    # Test memory management random 100 neurons
    def test_memory_management_random_100neurons(self):
        """
        Test memory management random 100 neurons
        """
        # Test with random matrix
        self.memory_management(
            data_dir="memory_management",
            use_matlab_params=False,
            precision=0.000001,
            torch_seed=5,
            np_seed=5,
            expected_NRMSEs=[
                1.1544502340257168e-02,
                9.5921922475099564e-03,
                1.0274781379848719e-03,
                3.5200463607907295e-03,
                6.2437158077955246e-02,
                1.1544502340257168e-02,
                9.5921922475099564e-03,
                1.0274781379848719e-03,
                5.1192387938499451e-02,
                5.9445840306580067e-03,
                1.8144855275750160e-02,
                9.4426041468977928e-03,
                2.1960476413369179e-02,
                5.6651360355317593e-03,
                6.4829468727111816e-02,
                1.7635645866394043e+00
            ]
        )
    # end test_memory_management_random_100neurons

    # Test memory management (input recreation) random 100 neurons
    def test_memory_management_input_recreation_random_100neurons(self):
        """
        Test memory management (input recreation) random 100 neurons
        """
        # Test with random matrix
        self.memory_management(
            data_dir="memory_management",
            use_matlab_params=False,
            loading_method=ecnc.SPESNCell.INPUTS_RECREATION,
            precision=0.000001,
            torch_seed=5,
            np_seed=5,
            expected_NRMSEs=[
                1.1544502340257168e-02,
                9.5921922475099564e-03,
                1.0274781379848719e-03,
                3.5200463607907295e-03,
                6.2437158077955246e-02,
                1.1544502340257168e-02,
                9.5921922475099564e-03,
                1.0274781379848719e-03,
                5.1192387938499451e-02,
                5.9445840306580067e-03,
                1.8144855275750160e-02,
                9.4426041468977928e-03,
                2.1960476413369179e-02,
                5.6651360355317593e-03,
                6.4829468727111816e-02,
                1.7635645866394043e+00
            ]
        )
    # end test_memory_management_input_recreation_random_100neurons

    # Test memory management random 200 neurons
    def test_memory_management_random_200neurons(self):
        """
        Test memory management random 200 neurons
        """
        # Test with random matrix
        self.memory_management(
            data_dir="memory_management",
            reservoir_size=200,
            use_matlab_params=False,
            precision=0.000001,
            torch_seed=5,
            np_seed=5,
            expected_NRMSEs=[
                0.0004915953031741,
                0.0016071919817477,
                0.0002676959265955,
                0.0009588617249392,
                0.0002541547582950,
                0.0004915953031741,
                0.0016071919817477,
                0.0002676959265955,
                0.0014735902659595,
                0.0008529321057722,
                0.0006031005177647,
                0.0015809513861313,
                0.0016617941437289,
                0.0003109153185505,
                0.0027175231371075,
                0.0012399877887219
            ]
        )
    # end test_memory_management_random_200neurons

    # Test memory management (input recreation) random 200 neurons
    def test_memory_management_input_recreation_random_200neurons(self):
        """
        Test memory management (input recreation) random 200 neurons
        """
        # Test with random matrix
        self.memory_management(
            data_dir="memory_management",
            reservoir_size=200,
            use_matlab_params=False,
            loading_method=ecnc.SPESNCell.INPUTS_RECREATION,
            precision=0.000001,
            torch_seed=5,
            np_seed=5,
            expected_NRMSEs=[
                0.0004915953031741,
                0.0016071919817477,
                0.0002676959265955,
                0.0009588617249392,
                0.0002541547582950,
                0.0004915953031741,
                0.0016071919817477,
                0.0002676959265955,
                0.0014735902659595,
                0.0008529321057722,
                0.0006031005177647,
                0.0015809513861313,
                0.0016617941437289,
                0.0003109153185505,
                0.0027175231371075,
                0.0012399877887219
            ]
        )
    # end test_memory_management_random_200neurons

    # endregion TEST

    # endregion BODY
# end Test_Memory_Management