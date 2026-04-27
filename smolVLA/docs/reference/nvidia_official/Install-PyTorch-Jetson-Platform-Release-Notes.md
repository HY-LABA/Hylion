# PyTorch for Jetson Platform — Release Notes

> Source PDF: `docs/reference/Install-PyTorch-Jetson-Platform-Release-Notes.pdf`  
> SWE-SWDOCTFX-001-RELN_v001 | April 2026

## Table of Contents

- Chapter 1. Overview
- Chapter 2. PyTorch for Jetson Platform

---

## Chapter 1. Overview

PyTorch (for JetPack) is an optimized tensor library for deep learning, using GPUs and CPUs. These NVIDIA-provided redistributables are Python pip wheel installers for PyTorch, with GPU-acceleration and support for cuDNN. The packages are intended to be installed on top of the specified version of JetPack.

**Supported platforms:**
- Jetson AGX Xavier
- Jetson AGX Orin
- Jetson Xavier NX

---

## Chapter 2. PyTorch for Jetson Platform

### Key Features and Enhancements

- **23.11 release**: NVIDIA optimized PyTorch docker containers now support iGPU architectures, including some Jetson devices.
- **24.06 release**: `cusparselt` support has been enabled for Jetson Platform.
- **26.03 release (Note)**: NVIDIA will **no longer produce** the standalone iGPU containers starting from this release.

---

### Compatibility Matrix

**Table 1. PyTorch compatibility with NVIDIA containers and JetPack**

| PyTorch Version | NVIDIA Framework Container | NVIDIA Framework Wheel | JetPack Version |
|---|---|---|---|
| 2.11.0a0+a6c236b9fd1 | 26.03 | - | 7.1 |
| 2.11.0a0+eb65b36914 | 26.02 | - | 7.1 |
| 2.10.0a0+a36e1d39eb | 26.01 | - | 7.1 |
| 2.10.0a0+b4e4ee81d3 | 25.12 | - | 7.1 |
| 2.10.0a0+b558c986e8 | 25.11 | - | 7.0 |
| 2.9.0a0+145a3a7bda | 25.10 | - | 7.0 |
| 2.9.0a0+50eac811a6 | 25.09 | - | 7.0 |
| 2.8.0a0+34c6371d24 | 25.08 | - | 7.0 |
| 2.8.0a0+5228986c39 | 25.06 | - | **6.2** |
| 2.8.0a0+5228986c39 | 25.05 | - | **6.2** |
| 2.7.0a0+79aa17489c | 25.04 | - | **6.2** |
| 2.7.0a0+7c8ec84dab | 25.03 | - | **6.2** |
| 2.7.0a0+6c54963f75 | 25.02 | - | **6.2** |
| 2.6.0a0+ecf3bae40a | 25.01 | - | 6.1 |
| 2.6.0a0+df5bbc09d1 | 24.12 | - | 6.1 |
| 2.6.0a0+df5bbc0 | 24.11 | - | 6.1 |
| 2.5.0a0+e000cf0ad9 | 24.10 | - | 6.1 |
| 2.5.0a0+b465a5843b | 24.09 | **24.09** | 6.1 |
| 2.5.0a0+872d972e41 | 24.08 | - | 6.0 |
| 2.4.0a0+3bcc3cddb5 | 24.07 | **24.07** | 6.0 |
| 2.4.0a0+f70bd71a48 | 24.06 | **24.06** | 6.0 |
| 2.4.0a0+07cecf4168 | 24.05 | **24.05** | 6.0 |
| 2.3.0a0+6ddf5cf85e | 24.04 | **24.04** | 6.0 Developer Preview |
| 2.3.0a0+40ec155e58 | 24.03 | **24.03** | - |
| 2.3.0a0+ebedce2 | 24.02 | **24.02** | - |
| 2.2.0a0+81ea7a4 | 23.12, 24.01 | **23.12, 24.01** | - |
| 2.2.0a0+6a974bec | 23.11 | - | - |
| 2.1.0a | 23.06 | - | 5.1.x |
| 2.0.0 | - | **23.05** | - |
| 2.0.0a0+fe05266f | - | **23.04** | - |
| 2.0.0a0+8aa34602 | - | **23.03** | - |
| 1.14.0a0+44dac51c | - | **23.02, 23.01** | - |
| 1.13.0a0+936e930 | - | **22.11** | 5.0.2 |
| 1.13.0a0+d0d6b1f | - | **22.09, 22.10** | - |
| 1.13.0a0+08820cb | 22.07 | **22.07** | - |
| 1.13.0a0+340c412 | 22.06 | **22.06** | 5.0.1 |
| 1.12.0a0+8a1a93a9 | 22.05 | **22.05** | 5.0 |
| 1.12.0a0+bd13bc66 | - | **22.04** | - |
| 1.12.0a0+2c916ef | - | **22.03** | - |
| 1.11.0a0+bfe5ad28 | - | **22.01** | 4.6.1 |

---

### Using PyTorch with the Jetson Platform

**Storage:** If you need more storage, we recommend connecting an external SSD via SATA on TX2 or Xavier devices, or USB on Jetson Nano.

---

### Known Issues

- TensorRT Model Optimizer is a new module but is **not yet supported on Jetson** due to its dependency on pytorch distributed functionality, which was disabled for Jetson.
