# Install-PyTorch-Jetson-Platform (Searchable Extract)

> Source PDF: `docs/reference/Install-PyTorch-Jetson-Platform.pdf`

Installing PyTorch For Jetson
Platform
Installation Guide

SWE-SWDOCTFX-001-INST _v001

|

April 2026

Table of Contents
Chapter 1. Overview................................................................................................................................ 1
1.1. Benefits of PyTorch for Jetson Platform............................................................................................. 1

Chapter 2. Prerequisites and Installation.......................................................................................3
2.1. Installing Multiple PyTorch Versions....................................................................................................... 4
2.2. Upgrading PyTorch...........................................................................................................................................4

Chapter 3. Verifying The Installation............................................................................................... 5
Chapter 4. Uninstalling...........................................................................................................................6
Chapter 5. Troubleshooting..................................................................................................................7

Installing PyTorch For Jetson Platform

SWE-SWDOCTFX-001-INST _v001 | ii

Chapter 1. Overview

PyTorch on Jetson Platform
PyTorch (for JetPack) is an optimized tensor library for deep learning, using GPUs and
CPUs. Automatic differentiation is done with a tape-based system at both a functional
and neural network layer level. This functionality brings a high level of flexibility, speed
as a deep learning framework, and provides accelerated NumPy-like functionality. These
NVIDIA-provided redistributables are Python pip wheel installers for PyTorch, with GPUacceleration and support for cuDNN. The packages are intended to be installed on top of
the specified version of JetPack as in the provided documentation.

Jetson AGX Xavier
The NVIDIA Jetson AGX Xavier developer kit for Jetson platform is the world's first AI
computer for autonomous machines. The Jetson AGX Xavier delivers the performance of
a GPU workstation in an embedded module under 30W.

Jetson AGX Orin
The NVIDIA Jetson AGX Orin Developer Kit includes a high-performance, power-efficient
Jetson AGX Orin module, and can emulate the other Jetson modules. You now have up
to 275 TOPS and 8X the performance of NVIDIA Jetson AGX Xavier in the same compact
form-factor for developing advanced robots and other autonomous machine products.

Jetson Xavier NX
The NVIDIA Jetson Xavier NX brings supercomputer performance to the edge in a small
form factor system-on-module. Up to 21 TOPS of accelerated computing delivers the
horsepower to run modern neural networks in parallel and process data from multiple
high-resolution sensors — a requirement for full AI systems.

1.1.

Benefits of PyTorch for Jetson
Platform

Installing PyTorch For Jetson Platform

SWE-SWDOCTFX-001-INST _v001 | 1

Overview

Installing PyTorch for Jetson Platform provides you with the access to the latest version
of the framework on a lightweight, mobile platform.

Installing PyTorch For Jetson Platform

SWE-SWDOCTFX-001-INST _v001 | 2

Chapter 2. Prerequisites and
Installation

Before you install PyTorch for Jetson, ensure you:
1. Install JetPack on your Jetson device.
2. Install system packages required by PyTorch:
sudo apt-get -y update;
sudo apt-get install -y

python3-pip libopenblas-dev;

3. If installing 24.06 PyTorch or later versions, cusparselt needs to be installed first:

wget
raw.githubusercontent.com/pytorch/pytorch/5c6af2b583709f6176898c017424dc9981023c28/.ci/
docker/
common/install_cusparselt.sh
export CUDA_VERSION=12.1 # as an example
bash ./install_cusparselt.sh

Next, install PyTorch with the following steps:
1. Export with the following command:
export TORCH_INSTALL=https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/
torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl

Or, download the wheel file and set.
export TORCH_INSTALL=path/to/torch-2.2.0a0+81ea7a4+nv23.12-cp38-cp38-linux_aarch64.whl

2. Install PyTorch.

python3 -m pip install --upgrade pip; python3 -m pip install numpy==’1.26.1’; python3 -m
pip install --no-cache $TORCH_INSTALL

If you want to install a specific version of PyTorch, replace TORCH_INSTALL with:

https://developer.download.nvidia.com/compute/redist/jp/v$JP_VERSION/pytorch/
$PYT_VERSION

Where:
JP_VERSION

The major and minor version of JetPack you are using, such as 461 for JetPack 4.6.1 or
50 for JetPack 5.0.

PYT_VERSION

The released version of the PyTorch wheels, as given in the Compatibility Matrix.

Installing PyTorch For Jetson Platform

SWE-SWDOCTFX-001-INST _v001 | 3

Prerequisites and Installation

2.1.

Installing Multiple PyTorch Versions

If you want to have multiple versions of PyTorch available at the same time, this can be
accomplished using virtual environments. See below.

Set up the Virtual Environment
First, install the virtualenv package and create a new Python 3 virtual environment:
$ sudo apt-get install virtualenv
$ python3 -m virtualenv -p python3 <chosen_venv_name>

Activate the Virtual Environment
Next, activate the virtual environment:
$ source <chosen_venv_name>/bin/activate

Install the desired version of PyTorch:
pip3 install --no-cache https://developer.download.nvidia.com/compute/redist/jp/v51/pytorch/
<torch_version_desired>

Deactivate the Virtual Environment
Finally, deactivate the virtual environment:
$ deactivate

Run a Specific Version of PyTorch
After the virtual environment has been set up, simply activate it to have access to the
specific version of PyTorch. Make sure to deactivate the environment after use:
$ source <chosen_venv_name>/bin/activate
$ <Run the desired PyTorch scripts>
$ deactivate

2.2.

Upgrading PyTorch

To upgrade to a more recent release of PyTorch, if one is available, uninstall the current
PyTorch version and refer to Prerequisites and Installation to install the new desired
release.

Installing PyTorch For Jetson Platform

SWE-SWDOCTFX-001-INST _v001 | 4

Chapter 3. Verifying The Installation

About this task
To verify that PyTorch has been successfully installed on the Jetson platform, you’ll need
to launch a Python prompt and import PyTorch.

Procedure
1. From the terminal, run:
$ export LD_LIBRARY_PATH=/usr/lib/llvm-8/lib:$LD_LIBRARY_PATH
$ python3

2. Import PyTorch:
>>> import torch

If PyTorch was installed correctly, this command should execute without error.

Installing PyTorch For Jetson Platform

SWE-SWDOCTFX-001-INST _v001 | 5

Chapter 4. Uninstalling

PyTorch can easily be uninstalled using the pip3 uninstall command, as below:
$ sudo pip3 uninstall -y torch

Installing PyTorch For Jetson Platform

SWE-SWDOCTFX-001-INST _v001 | 6

Chapter 5. Troubleshooting

Join the NVIDIA Jetson and Embedded Systems community to discuss Jetson platformspecific issues.

Installing PyTorch For Jetson Platform

SWE-SWDOCTFX-001-INST _v001 | 7

Notice
This document is provided for information purposes only and shall not be regarded as a warranty of a certain functionality, condition, or quality of a product.
NVIDIA Corporation (“NVIDIA”) makes no representations or warranties, expressed or implied, as to the accuracy or completeness of the information contained
in this document and assumes no responsibility for any errors contained herein. NVIDIA shall have no liability for the consequences or use of such information
or for any infringement of patents or other rights of third parties that may result from its use. This document is not a commitment to develop, release, or
deliver any Material (defined below), code, or functionality.
NVIDIA reserves the right to make corrections, modifications, enhancements, improvements, and any other changes to this document, at any time without
notice.
Customer should obtain the latest relevant information before placing orders and should verify that such information is current and complete.
NVIDIA products are sold subject to the NVIDIA standard terms and conditions of sale supplied at the time of order acknowledgement, unless otherwise
agreed in an individual sales agreement signed by authorized representatives of NVIDIA and customer (“Terms of Sale”). NVIDIA hereby expressly objects
to applying any customer general terms and conditions with regards to the purchase of the NVIDIA product referenced in this document. No contractual
obligations are formed either directly or indirectly by this document.
NVIDIA products are not designed, authorized, or warranted to be suitable for use in medical, military, aircraft, space, or life support equipment, nor in
applications where failure or malfunction of the NVIDIA product can reasonably be expected to result in personal injury, death, or property or environmental
damage. NVIDIA accepts no liability for inclusion and/or use of NVIDIA products in such equipment or applications and therefore such inclusion and/or use
is at customer’s own risk.
NVIDIA makes no representation or warranty that products based on this document will be suitable for any specified use. Testing of all parameters of each
product is not necessarily performed by NVIDIA. It is customer’s sole responsibility to evaluate and determine the applicability of any information contained
in this document, ensure the product is suitable and fit for the application planned by customer, and perform the necessary testing for the application in
order to avoid a default of the application or the product. Weaknesses in customer’s product designs may affect the quality and reliability of the NVIDIA
product and may result in additional or different conditions and/or requirements beyond those contained in this document. NVIDIA accepts no liability related
to any default, damage, costs, or problem which may be based on or attributable to: (i) the use of the NVIDIA product in any manner that is contrary to this
document or (ii) customer product designs.
No license, either expressed or implied, is granted under any NVIDIA patent right, copyright, or other NVIDIA intellectual property right under this document.
Information published by NVIDIA regarding third-party products or services does not constitute a license from NVIDIA to use such products or services or
a warranty or endorsement thereof. Use of such information may require a license from a third party under the patents or other intellectual property rights
of the third party, or a license from NVIDIA under the patents or other intellectual property rights of NVIDIA.
Reproduction of information in this document is permissible only if approved in advance by NVIDIA in writing, reproduced without alteration and in full
compliance with all applicable export laws and regulations, and accompanied by all associated conditions, limitations, and notices.
THIS DOCUMENT AND ALL NVIDIA DESIGN SPECIFICATIONS, REFERENCE BOARDS, FILES, DRAWINGS, DIAGNOSTICS, LISTS, AND OTHER DOCUMENTS
(TOGETHER AND SEPARATELY, “MATERIALS”) ARE BEING PROVIDED “AS IS.” NVIDIA MAKES NO WARRANTIES, EXPRESSED, IMPLIED, STATUTORY, OR
OTHERWISE WITH RESPECT TO THE MATERIALS, AND EXPRESSLY DISCLAIMS ALL IMPLIED WARRANTIES OF NONINFRINGEMENT, MERCHANTABILITY, AND
FITNESS FOR A PARTICULAR PURPOSE. TO THE EXTENT NOT PROHIBITED BY LAW, IN NO EVENT WILL NVIDIA BE LIABLE FOR ANY DAMAGES, INCLUDING
WITHOUT LIMITATION ANY DIRECT, INDIRECT, SPECIAL, INCIDENTAL, PUNITIVE, OR CONSEQUENTIAL DAMAGES, HOWEVER CAUSED AND REGARDLESS OF
THE THEORY OF LIABILITY, ARISING OUT OF ANY USE OF THIS DOCUMENT, EVEN IF NVIDIA HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
Notwithstanding any damages that customer might incur for any reason whatsoever, NVIDIA’s aggregate and cumulative liability towards customer for the
products described herein shall be limited in accordance with the Terms of Sale for the product.

HDMI
HDMI, the HDMI logo, and High-Definition Multimedia Interface are trademarks or registered trademarks of HDMI Licensing LLC.

OpenCL
OpenCL is a trademark of Apple Inc. used under license to the Khronos Group Inc.

NVIDIA Corporation | 2788 San Tomas Expressway, Santa Clara, CA 95051
https://www.nvidia.com

Trademarks
NVIDIA, the NVIDIA logo, and cuBLAS, CUDA, DALI, DGX, DGX-1, DGX-2, DGX Station, DLProf, Jetson, Kepler, Maxwell, NCCL, Nsight Compute, Nsight Systems,
NvCaffe, PerfWorks, Pascal, SDK Manager, Tegra, TensorRT, Triton Inference Server, Tesla, TF-TRT, and Volta are trademarks and/or registered trademarks of
NVIDIA Corporation in the U.S. and other countries. Other company and product names may be trademarks of the respective companies with which they
are associated.

Copyright
© 2022-2026 NVIDIA Corporation & Affiliates. All rights reserved.

NVIDIA Corporation | 2788 San Tomas Expressway, Santa Clara, CA 95051
https://www.nvidia.com

