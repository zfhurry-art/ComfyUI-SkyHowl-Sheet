# Troubleshooting / 排障

- 红色缺失节点 / Missing node: 根据DEPENDENCIES.md检查节点；不要通过批量升级整个环境解决。
- 模型不存在 / Missing model: 重新选择本机已有的UNet、CLIP和VAE。
- 输入文件不存在 / Missing input: female-reference.png只是占位名，必须加载实际参考图。
- 新代码未生效 / Stale backend: 重启ComfyUI并刷新浏览器。
- 图数不一致 / View count mismatch: 检查列表采样链路，不要重复图片补足格位。
- 背景接缝 / Background seams: 仅画布底色匹配，不修改原图；渐变和投影仍会保留。
- 后视短发 / Incorrect rear hairstyle: 检查提交提示词包含FINAL REAR HAIR LOCK，并提供清晰的发型参考；提示词不能保证所有种子都服从。
- 更新回退 / Rollback: 保留旧插件目录和工作流；停止目标服务后恢复备份并重启，不删除其他插件或模型。
