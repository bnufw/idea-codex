### Direction 1 | Shared Anchor + Residual Composition
- **Idea**: 保留一个全局共享 class-anchor space，每个任务只学 residual adapter / LoRA；训练时约束 residual 更新不能破坏旧类 anchor 的相对几何，推理时根据输入对多个 residual 做 soft composition，而不是硬 retrieval。
- **Why it fits the brief**: 训练侧负责“anchor 可比性”，推理侧负责“soft composition”，两者天然耦合。
- **Closest neighbors**: `Semantic Drift`, `SSIAT`, `MOS`, `CODA-Prompt`
- **Main risk**: reviewer 可能说这是 prototype + routing 的重组，除非你证明 soft composition 真比 retrieval 更稳。