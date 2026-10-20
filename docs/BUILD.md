# 构建说明

补丁产物是 .NET Framework 4.8 桌面程序，必须在 **Windows** 上构建。

## 环境

| 组件 | 用途 |
|---|---|
| .NET SDK 8.0 | 编译补丁器 `tools/RestorePclKz`（net8.0） |
| Python 3.12 + `dnfile==0.18.0`、`dncil==1.0.2` | 校验输入、抽取内嵌依赖、IL 校验 |
| Windows PowerShell 5.1（`powershell.exe`） | `jitcheck.ps1`：.NET Framework 程序集只能在 5.1 里加载并 JIT |
| 联网 | 仅用于下载 2.14 供体（上游固定提交，带哈希校验） |

## 本机构建

```powershell
python -m pip install dnfile==0.18.0 dncil==1.0.2
python tools/prepare_inputs.py
dotnet build tools/RestorePclKz/RestorePclKz.csproj --configuration Release --nologo
New-Item -ItemType Directory -Force artifacts | Out-Null
dotnet tools/RestorePclKz/bin/Release/net8.0/RestorePclKz.dll `
    build-inputs/donor-2.14.exe build-inputs/original.exe artifacts/PCL-2.99-snapshot-restored.exe
```

产物旁边会生成 `*.patch.json`，记录输入/输出哈希与每个被修改方法的 token 及说明。

## 验证

```powershell
dotnet tool install dotnet-ilverify --version 8.0.0 --tool-path .tools
python tools/verification/verify_binaries.py --original build-inputs/original.exe `
    --patched artifacts/PCL-2.99-snapshot-restored.exe `
    --ilverify .tools/ILVerify.exe --output verification

powershell -File tools/verification/jitcheck.ps1 `
    -Executable artifacts/PCL-2.99-snapshot-restored.exe `
    -PatchReport artifacts/PCL-2.99-snapshot-restored.exe.patch.json `
    -OutputDirectory jitcheck

pwsh -File tools/verification/smoke.ps1 `
    -Executable artifacts/PCL-2.99-snapshot-restored.exe `
    -OutputDirectory smoke-results
```

- `verify_binaries.py`：ILVerify 基线对比，拒绝新增错误与被改方法报错。
- `jitcheck.ps1`：CLR 逐个编译被改方法，`InvalidProgramException` 即失败；**这一步不能省**，ILVerify 抓不到导入器级别的非法 IL。
- `smoke.ps1`：干净目录启动，等标题窗口稳定 10 秒并截图。

## GitHub Actions

`.github/workflows/build.yml` 在 `windows-2022` 上执行上面全部步骤，产物为：

- `PCL-2.99-snapshot-restored`：恢复后的 EXE、`patch.json`、`inputs.json`、说明与 `SHA256SUMS.txt`
- `snapshot-restoration-verification`：`verification/`、`jitcheck/`、`smoke-results/`

改动 `input/`、`tools/` 或 workflow 会触发构建，也可以在 Actions 页面手动 `Run workflow`。
