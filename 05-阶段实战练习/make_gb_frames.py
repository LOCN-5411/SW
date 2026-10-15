# -*- coding: utf-8 -*-
"""
GB 图框 + 标题栏 生成器（阶段 4 用）
=================================================
输出：
  E:\\SW\\05-阶段实战练习\\GB-A3横.dxf      （420×297，留装订边）
  E:\\SW\\05-阶段实战练习\\GB-A4横.dxf      （297×210，留装订边）
  E:\\SW\\05-阶段实战练习\\preview\\GB-A3横.png
  E:\\SW\\05-阶段实战练习\\preview\\GB-A4横.png

⚠️ 关于尺寸的诚信声明（务必读）
--------------------------------------------------
1) 标题栏 180×56：GB/T 10609.1 的常用值，把握较大。
2) 图框边距：我**没有拿到标准原文**。GB/T 14689 的装订边 a 与其余边 c，
   我查到的两种说法互相冲突（a=20 与 a=25）。本脚本按下面参数生成，
   **请你对照教材/学校模板确认后改这两行再重新运行**：
        BIND_MARGIN = 25.0      # 装订边 a
        OTHER_MARGIN = 5.0      # 其余三边 c（A3/A4）
   常用候选组合：
        a=25, c=5   （我采用的，多数教材表格）
        a=20, c=5   （第三方资料的说法）
3) 标题栏内部分区是**实用简化版**，不是 GB/T 10609.1 的完整分区图
   （完整版含更改区/签字区/附加栏）。学生图纸用这个够，但要知道它是简化版。

DXF 只输出 LINE 实体（不含文字），因此不存在中文编码问题——
标题栏的文字请在 SolidWorks 图纸格式里自己加（一般还要链接到自定义属性）。
"""

import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT_DIR = r'E:\SW\05-阶段实战练习'
PREV_DIR = os.path.join(OUT_DIR, 'preview')
os.makedirs(PREV_DIR, exist_ok=True)

FONT = r'C:\Windows\Fonts\simhei.ttf'
font_manager.fontManager.addfont(FONT)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------------- 参数
BIND_MARGIN = 25.0        # 装订边 a（左侧）—— 见文件头说明，请自行核对
OTHER_MARGIN = 5.0        # 其余三边 c
TB_W, TB_H = 180.0, 56.0  # 标题栏 180×56（GB/T 10609.1）
CENTER_MARK = 5.0         # 对中符号：从纸边界画入图框内 5mm


def build_sheet(W, H):
    """返回 (粗线列表, 细线列表)。坐标原点在图纸左下角。"""
    thick, thin = [], []

    x_min, x_max = BIND_MARGIN, W - OTHER_MARGIN
    y_min, y_max = OTHER_MARGIN, H - OTHER_MARGIN

    # 纸边界（细线，仅示意；实际打印不需要）
    thin += [(0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]

    # 图框（粗线）
    thick += [(x_min, y_min, x_max, y_min), (x_max, y_min, x_max, y_max),
              (x_max, y_max, x_min, y_max), (x_min, y_max, x_min, y_min)]

    # 对中符号（粗线）：四边中点，从纸边界画入图框内 5mm
    cy, cx = H / 2.0, W / 2.0
    thick += [(cx, 0, cx, y_min + CENTER_MARK),           # 下
              (cx, H, cx, y_max - CENTER_MARK),           # 上
              (0, cy, x_min + CENTER_MARK, cy),           # 左
              (W, cy, x_max - CENTER_MARK, cy)]           # 右

    # ---- 标题栏（紧贴右下角内框线）----
    tx0, ty0 = x_max - TB_W, y_min
    tx1, ty1 = x_max, y_min + TB_H

    thick += [(tx0, ty0, tx1, ty0), (tx1, ty0, tx1, ty1),
              (tx1, ty1, tx0, ty1), (tx0, ty1, tx0, ty0)]

    # 横向分隔（自下而上）
    ys = [0.0, 13.0, 22.0, 31.0, 40.0, 48.0, 56.0]
    for y in ys[1:-1]:
        thin.append((tx0, ty0 + y, tx1, ty0 + y))

    # 纵向分隔：标签列 0–14，右侧标签列 122–136
    for x in (14.0, 122.0, 136.0):
        # 最下面一行（单位名称）整行贯通，不画竖线
        thin.append((tx0 + x, ty0 + 13.0, tx0 + x, ty1))

    rows = [(48.0, 56.0, '图名', '图号'),
            (40.0, 48.0, '材料', '比例'),
            (31.0, 40.0, '数量', '重量'),
            (22.0, 31.0, '设计', '日期'),
            (13.0, 22.0, '审核', '日期')]
    return thick, thin, (tx0, ty0, tx1, ty1), rows, (x_min, y_min, x_max, y_max)


def write_dxf(path, thick, thin):
    """最小 DXF R12 ASCII，仅 LINE 实体。"""
    buf = ['0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC\n',
           '0\nSECTION\n2\nTABLES\n0\nENDSEC\n',
           '0\nSECTION\n2\nENTITIES\n']
    for layer, segs in (('FRAME', thick), ('THIN', thin)):
        for x1, y1, x2, y2 in segs:
            buf.append('0\nLINE\n8\n%s\n10\n%.4f\n20\n%.4f\n30\n0.0\n'
                       '11\n%.4f\n21\n%.4f\n31\n0.0\n' % (layer, x1, y1, x2, y2))
    buf.append('0\nENDSEC\n0\nEOF\n')
    with open(path, 'w', encoding='ascii', errors='strict') as f:
        f.write(''.join(buf))


def render_png(path, W, H, thick, thin, tb, rows, frame, title):
    fig = plt.figure(figsize=(W / 25.4 * 0.6, H / 25.4 * 0.6), dpi=160)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_aspect('equal')
    ax.axis('off')
    for x1, y1, x2, y2 in thin:
        ax.plot([x1, x2], [y1, y2], color='#888888', lw=0.5)
    for x1, y1, x2, y2 in thick:
        ax.plot([x1, x2], [y1, y2], color='#000000', lw=1.5)

    tx0, ty0, tx1, ty1 = tb
    for (ya, yb, l1, l2) in rows:
        ax.text(tx0 + 2, ty0 + (ya + yb) / 2, l1, fontsize=6,
                ha='left', va='center', color='#c00000')
        ax.text(tx0 + 124, ty0 + (ya + yb) / 2, l2, fontsize=6,
                ha='left', va='center', color='#c00000')
    ax.text(tx0 + 2, ty0 + 6.5, '单位名称', fontsize=6, ha='left', va='center',
            color='#c00000')
    ax.text(tx0 + 16, ty0 + 6.5, '（此格通常放学校/学院名称）', fontsize=5.5,
            ha='left', va='center', color='#999999')

    x_min, y_min, x_max, y_max = frame
    ax.text((x_min + x_max) / 2, y_max - 12, title, fontsize=11, ha='center',
            va='center', color='#333333')
    ax.text(x_min + 2, y_min + 2, '装订边 a=%.0f' % BIND_MARGIN, fontsize=5.5,
            ha='left', va='bottom', color='#0066cc')
    ax.text(x_max - 2, y_max - 2, '其余三边 c=%.0f' % OTHER_MARGIN, fontsize=5.5,
            ha='right', va='top', color='#0066cc')
    ax.set_xlim(-8, W + 8)
    ax.set_ylim(-8, H + 8)
    fig.savefig(path, facecolor='white')
    plt.close(fig)


SHEETS = [('GB-A3横', 420.0, 297.0, 'A3 横放 420×297  ·  图框 + 标题栏（GB/T 10609.1 180×56）'),
          ('GB-A4横', 297.0, 210.0, 'A4 横放 297×210  ·  图框 + 标题栏（GB/T 10609.1 180×56）')]

for name, W, H, title in SHEETS:
    thick, thin, tb, rows, frame = build_sheet(W, H)
    dxf = os.path.join(OUT_DIR, name + '.dxf')
    png = os.path.join(PREV_DIR, name + '.png')
    write_dxf(dxf, thick, thin)
    render_png(png, W, H, thick, thin, tb, rows, frame, title)
    print('OK  %-10s  DXF %d 线  ->  %s' % (name, len(thick) + len(thin), dxf))
    print('             预览 -> %s' % png)

print('完成。装订边 a=%.0f，其余边 c=%.0f（如需修改，改脚本顶部两行后重跑）'
      % (BIND_MARGIN, OTHER_MARGIN))
