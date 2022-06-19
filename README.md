# llvm-installer

https://pypi.org/project/llvm-installer/

Helps installing pre-built LLVM packages for various operating systems.

## Usage as module

Getting LLVM installation URL for a particular OS/version/architecture.

```python
from llvm_installer import LlvmInstaller
import sys_detection

local_sys_conf = sys_detection.local_sys_conf()
llvm_installer = LlvmInstaller(
    short_os_name_and_version=local_sys_conf.short_os_name_and_version(),
    architecture=local_sys_conf.architecture)
llvm_url = llvm_installer.get_llvm_url(major_llvm_version=major_llvm_version)
```

## Command-line usage

```bash
python3 -m llvm_installer
```
