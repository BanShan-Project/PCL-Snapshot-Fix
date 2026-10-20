# PCL 快照版恢复（PCL-KZ-Fix）

把官方 PCL **2.99.0.0 快照版**（build 414）里因合规原因下线的 MC 下载、整合包导入与安装恢复回来，并关闭启动器云控与自更新。

做法与正式版恢复方案一致：对**校验过的官方 EXE** 做 IL 修改（Mono.Cecil），不重新编译源码，因此保留了原程序的登录与下载鉴权实现。

| 项 | 内容 |
|---|---|
| 输入 | `input/official-snapshot.exe`（官方快照版，5,985,280 字节） |
| 输入 SHA-256 | `5b64d6d540c376390470cea3ab99d47661e8bca81be2ba647ea83e7d2e9428fa` |
| 产物 | `PCL-2.99-snapshot-restored.exe`（由 GitHub Actions 生成，不提交到仓库） |
| 供体 | 上游提交 `5ef81e4` 的 2.14 正式版（补丁脚本自动下载并校验哈希） |

使用方式、改动范围与验证边界见 [快照版恢复说明](docs/RESTORATION-KZ.md)；本机构建与 Actions 说明见 [构建说明](docs/BUILD.md)。

## 构建

推送到 `main`（改动 `input/`、`tools/` 或 workflow）或手动触发 `Restore snapshot downloads`，会在 `windows-2022` 上：

1. 校验提交的官方快照版哈希，下载并校验 2.14 供体；
2. 编译补丁器并对官方 EXE 打补丁；
3. ILVerify 与原始 EXE 逐方法对比；
4. 让 CLR 逐个编译被修改的方法（`jitcheck`）；
5. 开窗冒烟测试；
6. 上传 `PCL-2.99-snapshot-restored` 与 `snapshot-restoration-verification` 两个产物。

## 免责

- 需要 Windows 程序本体与 .NET Framework 4.8；这不是 Android 应用。
- 本仓库只提供补丁工具、校验过的输入与说明，产物由 Actions 生成。
- PCL 的使用受《PCL 分发有限许可》约束，恢复被官方下线的功能属于逐例判断的范围，请自行评估后再分发产物。
