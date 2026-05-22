"""
Mock 虚拟试衣模型
────────────────
实现思路（仅用于演示）：
1. 将人像图片调整为统一尺寸 (640×960)
2. 将衣服图片缩放后覆盖到人像的胸部区域（上半身）
3. 为衣服区域叠加半透明混合，使效果更自然
4. 保存为 JPEG
"""

import io
from PIL import Image, ImageEnhance, ImageFilter


CANVAS_W = 640
CANVAS_H = 960

# 衣服覆盖区域（相对于画布）
CLOTH_X_START = 80       # 左边距
CLOTH_Y_START = 220      # 上边距（颈部以下）
CLOTH_W = 480            # 衣服宽度
CLOTH_H = 360            # 衣服高度


def mock_virtual_tryon(
    person_bytes: bytes,
    cloth_bytes: bytes,
    output_path: str,
) -> None:
    """
    将衣服图片叠加到人像图片上，保存结果到 output_path。

    Parameters
    ----------
    person_bytes : bytes  人像图片的原始字节
    cloth_bytes  : bytes  衣服图片的原始字节
    output_path  : str    结果图片保存路径
    """
    # ── 1. 打开图片 ────────────────────────────────────────────────────────
    person_img = Image.open(io.BytesIO(person_bytes)).convert("RGBA")
    cloth_img  = Image.open(io.BytesIO(cloth_bytes)).convert("RGBA")

    # ── 2. 调整人像尺寸 ────────────────────────────────────────────────────
    person_img = person_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)

    # ── 3. 调整衣服尺寸 ────────────────────────────────────────────────────
    cloth_resized = cloth_img.resize((CLOTH_W, CLOTH_H), Image.LANCZOS)

    # ── 4. 为衣服图层增加透明度（0.82 = 82% 不透明）使其与人像融合 ────────
    r, g, b, a = cloth_resized.split()
    a = ImageEnhance.Brightness(a).enhance(0.82)
    cloth_resized = Image.merge("RGBA", (r, g, b, a))

    # ── 5. 对衣服边缘做轻微模糊，减少硬边 ────────────────────────────────
    cloth_resized = cloth_resized.filter(ImageFilter.GaussianBlur(radius=1))

    # ── 6. 将衣服粘贴到人像上 ────────────────────────────────────────────
    canvas = person_img.copy()
    canvas.paste(cloth_resized, (CLOTH_X_START, CLOTH_Y_START), cloth_resized)

    # ── 7. 转换为 RGB 并保存（JPEG 不支持透明通道）────────────────────────
    result = canvas.convert("RGB")
    result.save(output_path, format="JPEG", quality=92)
