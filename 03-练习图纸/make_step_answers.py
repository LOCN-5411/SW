# -*- coding: utf-8 -*-
"""
把练习 06–10 建成实体并导出 STEP（参考答案）
=================================================
用途：
  1. 学员建完模后，用 eDrawings / 任意 STEP 查看器对照
  2. 独立验证图纸几何 —— 实体能建出来且 is_valid，说明轮廓闭合、尺寸自洽

几何来源：全部取自 generate_drawings.py 里 p06–p10 的实际坐标，
         不是凭记忆重写（见各函数注释里的出处行号）。

坐标约定：X 向右、Y 向里（深度）、Z 向上，单位 mm。
运行：python make_step_answers.py
"""

import os
import math
from build123d import (
    BuildPart, BuildSketch, BuildLine, Box, Cylinder, Polyline, make_face,
    extrude, revolve, fillet, chamfer, Locations, PolarLocations, Plane, Axis,
    Align, Mode, GeomType, export_step,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'STEP-参考答案')
os.makedirs(OUT, exist_ok=True)

MIN = (Align.MIN, Align.MIN, Align.MIN)
results = []


def report(name, part, path):
    bb = part.bounding_box()
    results.append((name, part.is_valid, part.volume / 1000.0,
                    bb.size.X, bb.size.Y, bb.size.Z, path))
    export_step(part, path)


# ============================================================ 练习 06
def ex06():
    """L 型支架。来源 generate_drawings.py p06（596–660 行）
    底板 X0–80 / Y0–60 / Z0–10；立板 Y50–60、Z10–60；
    φ20 通孔轴线沿 Y、孔心 (X40, Z35)；4×φ8 轴线沿 Z、(X,Y)=(10,10)(70,10)(10,50)(70,50)；
    三角筋 X36–44，剖面 (Y,Z)=(50,10)(20,10)(50,25)。"""
    with BuildPart() as p:
        Box(80, 60, 10, align=MIN)                                  # 底板
        with Locations((0, 50, 10)):
            Box(80, 10, 50, align=MIN)                              # 立板
        with BuildSketch(Plane.YZ.offset(36)) as sk:                # 三角筋（草图在 YZ 面）
            with BuildLine():
                Polyline((50, 10), (20, 10), (50, 25), (50, 10))
            make_face()
        extrude(amount=8)                                           # 沿 +X 拉 8 → X36–44
        with Locations((40, 30, 35)):                               # φ20 通孔
            Cylinder(10, 80, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
        with Locations((10, 10, 5), (70, 10, 5), (10, 50, 5), (70, 50, 5)):
            Cylinder(4, 20, mode=Mode.SUBTRACT)                     # 4×φ8 通孔
    return p.part


# ============================================================ 练习 07
def ex07():
    """法兰盘。来源 p07（663–707 行）
    φ120 外径、φ50 内孔、厚 20；6×φ11 在 PCD φ90 上、起始角 30°；
    外圆 C2 倒角、内孔 C1 倒角。"""
    with BuildPart() as p:
        Cylinder(60, 20)                                            # φ120 × 20
        Cylinder(25, 22, mode=Mode.SUBTRACT)                        # φ50 内孔
        with PolarLocations(45, 6, start_angle=30):
            Cylinder(5.5, 22, mode=Mode.SUBTRACT)                   # 6×φ11
        outer = p.edges().filter_by(GeomType.CIRCLE).filter_by(
            lambda e: abs(e.radius - 60) < 0.01)
        chamfer(outer, length=2)                                    # 外圆 C2
        bore = p.edges().filter_by(GeomType.CIRCLE).filter_by(
            lambda e: abs(e.radius - 25) < 0.01)
        chamfer(bore, length=1)                                     # 内孔 C1
    return p.part


# ============================================================ 练习 08
def ex08():
    """阶梯轴。来源 p08（710–758 行）的 upper/lower 折线
    φ30×40 → 退刀槽 → φ45×50 → 退刀槽 → φ35×40 → φ25×20，总长 150；
    两端 C1.5；键槽 宽8×深4×长30（X50–80，槽底 r18.5）；
    退刀槽 X87–90 槽底 r16、X127–130 槽底 r11。

    ⚠️ 注意：图纸主视图上 X50–80 处的缺口是【键槽的侧影】，不是整圈环槽。
    旋转剖面时该段必须用 φ45 的实际半径 22.5，键槽另用立方体单独切除。
    若照抄侧影轮廓去旋转，会得到一个 360° 的环形凹槽（体积会少约 15 cm³）。"""
    prof = [(0, 0), (0, 13.5), (1.5, 15), (40, 15), (40, 22.5),
            (87, 22.5), (87, 16), (90, 16), (90, 17.5),          # 退刀槽 1
            (127, 17.5), (127, 11), (130, 11), (130, 12.5),      # 退刀槽 2
            (148.5, 12.5), (150, 11), (150, 0)]
    with BuildPart() as p:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(*prof, close=True)
            make_face()
        revolve(axis=Axis.X)
        with Locations((65, 0, 18.5 + 5)):
            Box(30, 8, 10, mode=Mode.SUBTRACT)                      # 键槽 X50–80，切到 Z18.5
    return p.part


# ============================================================ 练习 09
def ex09():
    """减重带轮。来源 p09（761–817 行）
    外径 φ80、轮缘轴向 25、轮毂 φ34×40（两侧各凸 7.5）、孔 φ16、
    键槽 5×2.5（自孔壁算）、4×φ12 减重孔 PCD φ55 在 0/90/180/270、锐边 C1。
    此处以轴向为 X 建模（图纸上轴线沿 Y，仅朝向不同，形状一致）。"""
    half = [(-20, 8), (-20, 17), (-12.5, 17), (-12.5, 40),
            (12.5, 40), (12.5, 17), (20, 17), (20, 8)]
    with BuildPart() as p:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(*half, close=True)
            make_face()
        revolve(axis=Axis.X)
        with Locations((0, 0, 0)):
            with Locations((0, 27.5, 0)):
                Cylinder(6, 30, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
            with Locations((0, -27.5, 0)):
                Cylinder(6, 30, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
            with Locations((0, 27.5, 0)):
                Cylinder(6, 30, rotation=(0, 0, 0), mode=Mode.SUBTRACT)
            with Locations((0, -27.5, 0)):
                Cylinder(6, 30, rotation=(0, 0, 0), mode=Mode.SUBTRACT)
        with Locations((0, 0, 10.5 + 5)):                          # 键槽
            Box(30, 5, 10, mode=Mode.SUBTRACT)
        outer = p.edges().filter_by(GeomType.CIRCLE).filter_by(
            lambda e: abs(e.radius - 40) < 0.01)
        chamfer(outer, length=1)
    return p.part


# ============================================================ 练习 10
def ex10():
    """轴承座。来源 p10（820–888 行）
    底座 100×40×12（四角 R3）；两片立壁 X30–40 与 60–70、Y0–40、Z12–45；
    凸台 φ50 轴线沿 X、X40–60、轴线中心 (Y20, Z45)；轴承孔 φ32 沿 X 贯穿；
    2×φ11 安装孔 X15/85、Y 居中；凸台根部 R3。"""
    with BuildPart() as p:
        Box(100, 40, 12, align=MIN)                                 # 底座
        with Locations((30, 0, 12)):
            Box(10, 40, 33, align=MIN)                              # 左立壁
        with Locations((60, 0, 12)):
            Box(10, 40, 33, align=MIN)                              # 右立壁
        with Locations((50, 20, 45)):
            Cylinder(25, 20, rotation=(0, 90, 0))                   # 凸台 φ50 × 20
        with Locations((50, 20, 45)):
            Cylinder(16, 90, rotation=(0, 90, 0), mode=Mode.SUBTRACT)   # 轴承孔 φ32
        with Locations((15, 20, 6), (85, 20, 6)):
            Cylinder(5.5, 30, mode=Mode.SUBTRACT)                   # 2×φ11
        # 底座四角 R3
        corners = [e for e in p.edges().filter_by(Axis.Z)
                   if abs(e.length - 12) < 0.01
                   and (abs(e.center().X) < 0.01 or abs(e.center().X - 100) < 0.01)
                   and (abs(e.center().Y) < 0.01 or abs(e.center().Y - 40) < 0.01)]
        if corners:
            fillet(corners, radius=3)
    return p.part


JOBS = [('练习06-L型支架', ex06), ('练习07-法兰盘', ex07), ('练习08-阶梯轴', ex08),
        ('练习09-减重带轮', ex09), ('练习10-轴承座', ex10)]

print('%-18s %-8s %10s  %-22s' % ('零件', 'is_valid', '体积cm³', '包围盒 X×Y×Z'))
print('-' * 74)
for name, fn in JOBS:
    try:
        part = fn()
        path = os.path.join(OUT, name + '.step')
        report(name, part, path)
        bb = part.bounding_box()
        print('%-18s %-8s %10.2f  %.1f × %.1f × %.1f' %
              (name, part.is_valid, part.volume / 1000.0,
               bb.size.X, bb.size.Y, bb.size.Z))
    except Exception as e:
        print('%-18s FAILED: %s: %s' % (name, type(e).__name__, e))

print('-' * 74)
print('输出目录:', OUT)
