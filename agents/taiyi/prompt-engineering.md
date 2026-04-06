# Prompt Engineering 完全指南 👑

> **版本**: 2026.04 | **整理者**: 太一 | **适用**: Midjourney/Stable Diffusion/AI 视频生成

---

## 一、核心心法

### 1.1 Prompt 的本质

Prompt 不是"描述"，而是**导演脚本**。你不是在告诉 AI"有什么"，而是在指导它"如何呈现"。

```
 vague: "一个女人在森林里"
 ↓
 directed: "30 岁女性精灵猎人，晨雾中的古老森林，丁达尔光线，电影级景深，8K"
```

### 1.2 通用公式（万能框架）

```
[主体描述] + [环境/场景] + [风格/媒介] + [构图/视角] + [光线/色彩] + [技术参数]
```

---

## 二、Midjourney 专项技巧（V7 版）

### 2.1 核心参数速查

| 参数 | 作用 | 示例 |
|------|------|------|
| `--ar` | 宽高比 | `--ar 16:9` `--ar 3:4` |
| `--stylize` | 艺术化程度 (0-1000) | `--stylize 650` |
| `--v 7` | 使用 V7 模型 | `--v 7` |
| `--cref` | 角色参考（一致性） | `--cref https://img.url` |
| `--sref` | 风格参考（一致性） | `--sref https://img.url` |
| `--cw` | 角色参考权重 (0-100) | `--cw 80` |
| `--no` | 排除元素 | `--no text,watermark` |
| `--seed` | 固定随机种子 | `--seed 12345` |

### 2.2 角色一致性方案（🔴 重点）

**问题**: 如何让同一角色在多张图中保持外貌一致？

**解决方案**:

```bash
# 方案 1: Character Reference (--cref)
/imagine prompt: [新场景描述] --cref https://原图 URL --cw 80

# 方案 2: Omni Reference (V7 新特性)
/imagine prompt: [新场景描述] --oref https://参考图 URL

# 方案 3: 固定种子 + 微调
/imagine prompt: [角色描述], red hair, blue eyes --seed 12345
/imagine prompt: [角色描述], red hair, blue eyes, different pose --seed 12345
```

**权重说明**:
- `--cw 100`: 完整复制角色（脸 + 发型 + 服装）
- `--cw 80`: 复制脸 + 发型（推荐）
- `--cw 20`: 仅复制面部特征

### 2.3 风格一致性方案（🟡 重点）

```bash
# 使用 Style Reference
/imagine prompt: [内容描述] --sref https://风格参考图 URL

# 多风格融合
/imagine prompt: [内容] --sref https://img1.url --sref https://img2.url --sw 0.7

# 风格权重 (0-1000, 默认 100)
--sw 300  # 更强风格化
```

### 2.4 高级技巧

**多提示词权重**:
```
/imagine foggy forest::2 mysterious cabin::1 --v 7
# 森林权重是木屋的 2 倍
```

**局部重绘 (Remix Mode)**:
```
1. 开启 /settings → Remix Mode
2. 生成图片后点击 V 变体
3. 在弹出框中修改提示词
```

---

## 三、Stable Diffusion 专项技巧（SD3.5）

### 3.1 提示词结构

```
[风格定义] + [主体 + 动作] + [构图/视角] + [光线/色彩] + [技术参数]
```

### 3.2 Negative Prompt（负面提示词）🔴

**作用**: 告诉 AI"不要什么"，比正面描述更有效

**通用负面词库**:
```
low quality, blurry, artifacts, grainy, cropped, ugly, 
duplicated, hands, imperfect eyes, deformed pupils, 
deformed iris, text, watermark, signature, boring, 
bad anatomy, extra limbs, distorted face, mutation
```

**人像专用**:
```
bad hands, missing fingers, extra digit, fewer digits, 
cropped, worst quality, low quality, normal quality, 
jpeg artifacts, signature, watermark, username, blurry
```

**风景专用**:
```
text, watermark, signature, blurry, low quality, 
distorted buildings, crooked horizon, oversaturated
```

### 3.3 风格控制关键词

| 风格类型 | 关键词示例 |
|----------|-----------|
| 摄影 | `photorealistic, 85mm lens, f/1.8, bokeh` |
| 油画 | `oil painting, impasto, visible brushstrokes` |
| 水彩 | `watercolor, wet-on-wet, soft edges` |
| 数字艺术 | `digital art, concept art, artstation` |
| 动漫 | `anime, cel shaded, studio ghibli style` |
| 3D 渲染 | `3D render, octane render, unreal engine 5` |

### 3.4 构图术语

```
- 视角：bird's eye view, worm's eye view, eye level
- 景别：close-up, medium shot, wide shot, extreme wide shot
- 镜头：fish-eye lens, telephoto, macro, wide-angle
- 电影术语：dolly zoom, tracking shot, crane shot, Dutch angle
```

---

## 四、AI 视频生成专项技巧

### 4.1 主流平台对比

| 平台 | 擅长领域 | 时长限制 | Prompt 特点 |
|------|----------|----------|-------------|
| **Sora 2** | 电影级叙事 | ~60 秒 | 故事性强，需要完整场景描述 |
| **Runway Gen-4** | 营销/创意 | ~16 秒 | 支持镜头控制，可局部编辑 |
| **Pika 2.5** | 短视频/动画 | ~10 秒 | 简洁直接，适合循环动画 |
| **Kling 3.0** | 长视频 | ~3 分钟 | 支持多镜头叙事，原生音频 |

### 4.2 4C 模型框架（🔴 核心）

```
1. Concept（概念）: 视频的核心想法
2. Composition（构图）: 视觉和镜头设置
3. Color & Style（色彩风格）: 情绪、光线、色调
4. Continuity（连贯性）: 场景之间的流畅过渡
```

### 4.3 各平台 Prompt 公式

**Sora（叙事导向）**:
```
[场景] + [角色] + [动作] + [情绪] + [镜头]
示例: "An astronaut drifting through space debris, 
reflective helmet showing Earth below, melancholic mood, 
close-up camera, cinematic 8K."
```

**Runway（营销导向）**:
```
[主体] + [动作] + [风格] + [基调]
示例: "Fashion model walking down a futuristic runway, 
cyberpunk theme, vivid colors, confident tone."
```

**Pika（短视频导向）**:
```
[角色] + [环境] + [运动] + [风格]
示例: "A cute robot watering a plant on Mars, 
cheerful music, Pixar-style animation."
```

### 4.4 镜头运动术语

```
- camera movement: dolly in/out, pan left/right, tilt up/down
- zoom: slow zoom in, rapid zoom out
- tracking: following shot, tracking pan
- aerial: drone shot, bird's eye view, helicopter shot
- special: dolly zoom (vertigo effect), whip pan
```

---

## 五、10 个高质量 Prompt 示例

### 示例 1: 赛博朋克角色（Midjourney）
```
A female cyberpunk hacker with neon blue hair and 
cybernetic eye implants, standing on a rainy Tokyo 
rooftop at night, holographic advertisements reflecting 
in puddles, cinematic lighting, volumetric fog, 
photorealistic, 85mm lens --ar 16:9 --stylize 700 --v 7
```

### 示例 2: 古风仙侠（Midjourney）
```
一位白衣剑仙御剑飞行于云海之上，长发飘逸，
手持发光古剑，远处仙山若隐若现，中国水墨画风格，
留白构图，淡雅色彩 --ar 3:4 --stylize 500 --v 7
```

### 示例 3: 产品摄影（Stable Diffusion）
```
Professional product photography of a luxury perfume bottle, 
crystal clear glass with golden cap, soft studio lighting, 
white marble background, shallow depth of field, 
commercial advertising style, 8K resolution
Negative: text, watermark, blurry, distorted reflections
```

### 示例 4: 奇幻场景（Midjourney）
```
Ancient library inside a giant tree, spiral staircases 
made of living wood, glowing books floating in mid-air, 
magical particles in the air, warm ambient lighting, 
fantasy concept art, highly detailed --ar 16:9 --v 7
```

### 示例 5: 角色一致性工作流（Midjourney）
```
# 第一步：创建角色基准图
/imagine portrait of a young wizard with silver hair and 
purple robes, holding a crystal staff, studio lighting --seed 42

# 第二步：同一角色不同场景
/imagine the same young wizard casting a fire spell in 
a dark dungeon --cref [基准图 URL] --cw 80 --seed 42

# 第三步：角色特写
/imagine close-up of the young wizard's face, 
determined expression --cref [基准图 URL] --cw 100 --seed 42
```

### 示例 6: AI 视频 - 电影开场（Sora）
```
Opening scene of a sci-fi movie: massive spaceship emerging 
from hyperspace above an alien planet with purple oceans, 
camera slowly pushes in towards the ship's bridge, 
epic orchestral score, IMAX quality, Christopher Nolan style
```

### 示例 7: AI 视频 - 产品展示（Runway）
```
Luxury watch rotating on black velvet surface, 
dramatic side lighting highlighting the gold details, 
slow motion 60fps, commercial advertisement style, 
elegant and sophisticated tone
```

### 示例 8: AI 视频 - 动画循环（Pika）
```
Cute chibi character bouncing on a cloud, 
loop animation, pastel colors, kawaii style, 
soft shadows, 2D animation, cheerful mood
```

### 示例 9: 风格融合实验（Midjourney）
```
A steampunk dragon made of brass gears and copper pipes, 
breathing steam instead of fire, Victorian workshop background, 
mix of Jules Verne and Hayao Miyazaki styles, 
intricate mechanical details --ar 4:3 --sref [蒸汽朋克参考图] --v 7
```

### 示例 10: 多角色场景（Midjourney）
```
Three generations of warriors standing together: 
grandfather with battle scars and armor, father with 
tactical gear, young daughter with futuristic weapons, 
epic sunset battlefield, cinematic composition, 
character sheet style for consistency --ar 21:9 --v 7
```

---

## 六、实战工作流

### 6.1 角色设计工作流

```
1. 基准图生成
   → 正面肖像，简洁背景，--seed 固定

2. 角色一致性测试
   → 使用--cref 生成侧面/背面/不同表情

3. 场景适配
   → 保持--cref + --seed，更换场景描述

4. 风格统一
   → 确定最终风格后，用--sref 锁定
```

### 6.2 视频分镜工作流

```
1. 概念草图 (Midjourney)
   → 生成关键帧静态图

2. 动态化 (Runway/Pika)
   → 图生视频，添加镜头运动

3. 连贯性检查
   → 确保角色/风格在各镜头一致

4. 后期合成
   → 多段视频拼接 + 音效
```

### 6.3 批量生成技巧

```bash
# 使用种子批量测试
--seed 1001, --seed 1002, --seed 1003...

# 使用参数网格测试
--stylize 300/500/700 + --chaos 10/30/50

# 使用 Remix Mode 快速迭代
/settings → 开启 Remix → V 变体时修改提示词
```

---

## 七、常见问题速查

| 问题 | 解决方案 |
|------|----------|
| 角色长得不一样 | 使用 `--cref` + 固定`--seed` |
| 风格不统一 | 使用 `--sref` 锁定风格参考图 |
| 手部/脸部崩坏 | 添加负面词 `bad hands, deformed face` |
| 画面太乱 | 简化提示词，减少::权重分散 |
| 视频闪烁/变形 | 降低运动幅度，使用 image-to-video |
| 颜色太饱和 | 添加 `muted colors, natural tones` |

---

## 八、持续学习资源

- **Midjourney 官方**: discord.gg/midjourney
- **Prompt 库**: promptbase.com, lexica.art
- **风格参考**: artstation.com, pinterest.com
- **技术更新**: 关注各平台官方 Twitter/博客

---

> **太一批注**: Prompt 工程的核心不是背关键词，而是培养"导演思维"。每次写 Prompt 前，先问自己：我要什么情绪？什么视角？什么故事？剩下的，只是技术实现。👑

*最后更新：2026-04-05*
