# Dependencies / 依赖

- Python >=3.10; NumPy; Pillow; ComfyUI现有PyTorch运行环境。
- 工作流额外需要 `TextEncodeQwenImage21` 和 `QwenImage21Cache`。它们由 ComfyUI 官方 comfy_extras/nodes_qwen.py 提供，不属于本插件。官方来源：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_qwen.py 。需要包含这两个节点且输入契约兼容的ComfyUI版本；最低版本号尚未验证。
- 标准节点：UNETLoader、CLIPLoader、VAELoader、KSamplerSelect、ManualSigmas、SamplerCustom、VAEDecode、LoadImage、SaveImage。
- 本插件节点：SkyHowlCharacterSheetPanels、SkyHowlSheetCompose；旧V4节点ID继续保留。
- 模型控件的现有文件名仅是测试配置，使用前选择自己安装的兼容模型。模型、权重与外部插件不随包提供，遵守各自条款。
- 当前逐视图拼版不调用OpenCV头像定位或背景清理，不需要运行setup_head_focus.py。

The two Qwen-specific nodes must already exist in the target installation. Their official source is ComfyUI/comfy_extras/nodes_qwen.py. The supplied workflow inputs were checked against the official node schemas; the minimum compatible ComfyUI release has not been established. The supplied workflow is not a self-contained model distribution.
