#!/bin/bash
# 디바이스 환경 스냅샷 수집 스크립트 (원격 실행용 payload)
# 직접 실행하지 말고 run_snapshots.sh 를 사용하세요.
# 디바이스 종류(Orin / DGX Spark)를 자동 감지합니다.

# ─── 디바이스 감지 ───────────────────────────────────────────
if [ -f /etc/nv_tegra_release ]; then
  DEVICE_TYPE="orin"
else
  DEVICE_TYPE="dgx_spark"
fi

# ─────────────────────────────────────────────
# HARDWARE
# ─────────────────────────────────────────────

echo "### HOST"
hostname
date
echo "DEVICE_TYPE: $DEVICE_TYPE"
echo ""

if [ "$DEVICE_TYPE" = "orin" ]; then
  echo "### OS / JetPack / L4T"
  lsb_release -a 2>/dev/null
  cat /etc/nv_tegra_release 2>/dev/null
  cat /etc/nv_jetpack_version 2>/dev/null || echo "nv_jetpack_version not found"
  uname -a
else
  echo "### OS"
  lsb_release -a 2>/dev/null
  uname -a
fi
echo ""

echo "### CPU"
lscpu | grep -E "Architecture|Model name|Socket|Core|Thread|CPU\(s\)|MHz|NUMA"
echo ""

echo "### Memory"
free -h
echo ""

echo "### GPU (nvidia-smi)"
nvidia-smi 2>/dev/null || echo "nvidia-smi not available"
echo ""

if [ "$DEVICE_TYPE" = "orin" ]; then
  echo "### GPU (tegrastats snapshot)"
  timeout 2 tegrastats 2>/dev/null | head -3 || echo "tegrastats not available"
  echo ""

  echo "### nvpmodel"
  nvpmodel -q 2>/dev/null || echo "nvpmodel not available"
  nvpmodel -q --verbose 2>/dev/null
  echo ""
else
  echo "### GPU Detail"
  nvidia-smi --query-gpu=index,name,uuid,memory.total,memory.free,temperature.gpu,power.draw,driver_version \
    --format=csv 2>/dev/null || echo "nvidia-smi query failed"
  echo ""

  echo "### GPU Topology"
  nvidia-smi topo -m 2>/dev/null || echo "topology not available"
  echo ""
fi

# ─────────────────────────────────────────────
# SOFTWARE
# ─────────────────────────────────────────────

echo "### CUDA"
nvcc --version 2>/dev/null || echo "nvcc not found"
cat /usr/local/cuda/version.json 2>/dev/null || echo "CUDA version.json not found"
echo ""

echo "### cuDNN"
if [ "$DEVICE_TYPE" = "orin" ]; then
  cat /usr/include/aarch64-linux-gnu/cudnn_version.h 2>/dev/null | grep -E "CUDNN_MAJOR|CUDNN_MINOR|CUDNN_PATCH" \
    || dpkg -l libcudnn* 2>/dev/null | grep libcudnn \
    || echo "cuDNN not found"
else
  cat /usr/include/cudnn_version.h 2>/dev/null | grep -E "CUDNN_MAJOR|CUDNN_MINOR|CUDNN_PATCH" \
    || dpkg -l libcudnn* 2>/dev/null | grep libcudnn \
    || echo "cuDNN not found"
fi
echo ""

echo "### TensorRT"
dpkg -l tensorrt 2>/dev/null | grep tensorrt \
  || python3 -c "import tensorrt; print('TensorRT:', tensorrt.__version__)" 2>/dev/null \
  || echo "TensorRT not found"
echo ""

echo "### PyTorch"
python3 -c "
import torch
print('torch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
print('CUDA version:', torch.version.cuda)
print('Device count:', torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print(f'  GPU {i}:', torch.cuda.get_device_name(i))
" 2>/dev/null || echo "PyTorch not installed"
echo ""

echo "### Python"
python3 --version 2>/dev/null
pip3 list 2>/dev/null | grep -iE "torch|numpy|opencv|ros|transformers|huggingface|lerobot|smolvla|diffusers" \
  || echo "pip3 not available"
echo ""

if [ "$DEVICE_TYPE" = "dgx_spark" ]; then
  echo "### Conda Envs"
  conda env list 2>/dev/null || echo "conda not available"
  echo ""
fi

echo "### ROS2"
if ls /opt/ros/*/setup.bash 1>/dev/null 2>&1; then
  source /opt/ros/*/setup.bash 2>/dev/null
  ros2 --version 2>/dev/null || echo "ros2 not available"
  ros2 pkg list 2>/dev/null | head -20
else
  echo "ROS2 not found"
fi
echo ""

echo "### Docker"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null || echo "Docker not available"
echo ""
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>/dev/null
echo ""

echo "### SSH"
dpkg -l openssh-server 2>/dev/null | grep openssh-server
systemctl is-active ssh 2>/dev/null
systemctl is-enabled ssh 2>/dev/null
ss -tlnp | grep :22
echo ""

# ─────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────

echo "### LSBLK"
lsblk -o NAME,MODEL,SERIAL,SIZE,TYPE,TRAN,FSTYPE,UUID,MOUNTPOINT
echo ""

echo "### NVME"
nvme list 2>/dev/null || echo "nvme-cli not installed"
echo ""

echo "### DF"
df -h --output=source,fstype,size,used,avail,pcent,target 2>/dev/null | grep -vE "tmpfs|loop|udev"
echo ""

echo "### USB"
lsusb 2>/dev/null || echo "lsusb not available"
echo ""

echo "### MOUNT"
mount | grep -vE "tmpfs|loop|cgroup|proc|sys|dev|run|snap"
echo ""

echo "### FSTAB"
cat /etc/fstab
echo ""

# ─────────────────────────────────────────────
# NETWORK
# ─────────────────────────────────────────────

echo "### NETWORK INTERFACES"
ip addr show
echo ""

echo "### ROUTING TABLE"
ip route show
echo ""

echo "### DNS"
cat /etc/resolv.conf
echo ""

echo "### OPEN PORTS (LISTEN)"
ss -tlnp
echo ""

echo "### HOSTNAME & HOSTS"
hostname -f 2>/dev/null || hostname
cat /etc/hosts
echo ""

echo "### PING TEST"
ping -c 2 8.8.8.8 2>/dev/null && echo "[외부 인터넷 연결 OK]" || echo "[외부 인터넷 연결 실패]"
echo ""
