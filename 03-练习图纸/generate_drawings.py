# -*- coding: utf-8 -*-
"""
SolidWorks 零基础练习图纸 —— 生成脚本
=================================================
运行：
  C:\\Users\\lOCN\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe generate_drawings.py

输出：
  E:\\SW\\03-练习图纸\\SolidWorks-练习图纸.pdf      （A4 横向：封面 + 10 张练习）
  E:\\SW\\03-练习图纸\\preview\\练习01.png ... 练习10.png （150 dpi）

约定：
  * 单位 mm，图上数字不带单位后缀（制图惯例）
  * 第一角投影（GB）：主视图左上、俯视图在主视图正下方、左视图在主视图正右方
  * 括号尺寸 = 参考尺寸（由其它尺寸唯一确定，建模时不必再标）
  * 粗实线=可见轮廓；虚线=不可见轮廓；点划线=中心线；细实线=尺寸线/剖面线
本脚本可重复运行，输出完全一致。
"""

import os
import math

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

# --------------------------------------------------------------------------
# 0. 字体与全局样式
# --------------------------------------------------------------------------
FONT_SIMHEI = r'C:\Windows\Fonts\simhei.ttf'
if not os.path.exists(FONT_SIMHEI):
    raise SystemExit('找不到中文字体：' + FONT_SIMHEI)
font_manager.fontManager.addfont(FONT_SIMHEI)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams['lines.scale_dashes'] = False
plt.rcParams['savefig.facecolor'] = 'white'

A4W, A4H = 11.692913, 8.267717

LINE_STYLE = {
    'out':    (1.4, '#000000', '-'),
    'thin':   (0.65, '#000000', '-'),
    'hidden': (0.65, '#000000', (0, (4.5, 2.2))),
    'center': (0.7, '#c00000', (0, (14, 3, 1.6, 3))),
    'cut':    (1.1, '#c00000', (0, (16, 3, 1.6, 3))),
    'dim':    (0.6, '#000000', '-'),
    'ext':    (0.5, '#000000', '-'),
    'hatch':  (0.45, '#404040', '-'),
    'proj':   (0.5, '#a0a0a0', (0, (1.2, 3.0))),
    'frame':  (1.0, '#000000', '-'),
}

FS_DIM = 8.0
FS_LABEL = 8.2
FS_NOTE = 7.6


# --------------------------------------------------------------------------
# 1. 图幅类
# --------------------------------------------------------------------------
class Sheet:
    """一张 A4 横向图纸。数据坐标 = 零件真实 mm，等比例（aspect=equal）。"""

    def __init__(self, fig, rect, upp=0.25):
        self.fig = fig
        self.rect = rect
        self.upp = upp
        self.ax = fig.add_axes(rect)
        self.ax.set_aspect('equal', adjustable='box', anchor='C')
        self.ax.set_axis_off()
        self.x0, self.y0, self.x1, self.y1 = 1e18, 1e18, -1e18, -1e18

    def track(self, x, y):
        if x < self.x0:
            self.x0 = x
        if x > self.x1:
            self.x1 = x
        if y < self.y0:
            self.y0 = y
        if y > self.y1:
            self.y1 = y

    def track_pts(self, pts):
        for p in pts:
            self.track(p[0], p[1])

    def fit(self, pad=6.0):
        w = (self.x1 - self.x0) + 2 * pad
        h = (self.y1 - self.y0) + 2 * pad
        cx = (self.x0 + self.x1) / 2.0
        cy = (self.y0 + self.y1) / 2.0
        rw = self.rect[2] * A4W
        rh = self.rect[3] * A4H
        need = rw / rh
        if w / h > need:
            h = w / need
        else:
            w = h * need
        self.ax.set_xlim(cx - w / 2.0, cx + w / 2.0)
        self.ax.set_ylim(cy - h / 2.0, cy + h / 2.0)
        self.upp = w / (rw * 72.0)

    # ---- 图元 ------------------------------------------------------------
    def line(self, p1, p2, style='out', lw=None, color=None, track=True):
        lwv, cv, lsv = LINE_STYLE[style]
        self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], ls=lsv,
                     lw=(lw if lw else lwv), color=(color if color else cv),
                     solid_capstyle='butt', dash_capstyle='butt', zorder=3)
        if track:
            self.track_pts([p1, p2])

    def polyline(self, pts, style='out', closed=False, lw=None, color=None, track=True):
        if closed and pts[0] != pts[-1]:
            pts = list(pts) + [pts[0]]
        lwv, cv, lsv = LINE_STYLE[style]
        self.ax.plot([p[0] for p in pts], [p[1] for p in pts], ls=lsv,
                     lw=(lw if lw else lwv), color=(color if color else cv),
                     solid_capstyle='butt', solid_joinstyle='miter', zorder=3)
        if track:
            self.track_pts(pts)

    def circle(self, c, r, style='out', lw=None, color=None, n=241, track=True):
        pts = [(c[0] + r * math.cos(2 * math.pi * i / n),
                c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
        self.polyline(pts, style=style, lw=lw, color=color, track=False)
        if track:
            self.track(c[0] - r, c[1] - r)
            self.track(c[0] + r, c[1] + r)

    def ellipse(self, c, a, b, style='out', lw=None, color=None, n=241, track=True):
        pts = [(c[0] + a * math.cos(2 * math.pi * i / n),
                c[1] + b * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
        self.polyline(pts, style=style, lw=lw, color=color, track=False)
        if track:
            self.track(c[0] - a, c[1] - b)
            self.track(c[0] + a, c[1] + b)

    def arc(self, c, r, a1, a2, style='out', lw=None, color=None, track=True):
        n = max(10, int(abs(a2 - a1) / 2.5) + 2)
        pts = [(c[0] + r * math.cos(math.radians(a1 + (a2 - a1) * i / n)),
                c[1] + r * math.sin(math.radians(a1 + (a2 - a1) * i / n)))
               for i in range(n + 1)]
        self.polyline(pts, style=style, lw=lw, color=color, track=track)
        return pts

    def rect(self, p1, p2, style='out', lw=None, track=True):
        self.polyline([p1, (p2[0], p1[1]), p2, (p1[0], p2[1])], style=style,
                      closed=True, lw=lw, track=track)

    # ---- 中心线 ----------------------------------------------------------
    def cline(self, p1, p2, style='center', ext=2.5):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        L = math.hypot(dx, dy) or 1.0
        e = ext * self.upp
        self.line((p1[0] - dx / L * e, p1[1] - dy / L * e),
                  (p2[0] + dx / L * e, p2[1] + dy / L * e), style)

    def center_cross(self, c, r):
        e = 2.4 * self.upp
        self.line((c[0] - r - e, c[1]), (c[0] + r + e, c[1]), 'center')
        self.line((c[0], c[1] - r - e), (c[0], c[1] + r + e), 'center')

    # ---- 剖面线 ----------------------------------------------------------
    def hatch(self, pts, angle=45.0, spacing=None):
        if spacing is None:
            spacing = 8.0 * self.upp
        a = math.radians(angle)
        ca, sa = math.cos(a), math.sin(a)
        rp = [(x * ca + y * sa, -x * sa + y * ca) for x, y in pts]
        ymin = min(p[1] for p in rp)
        ymax = max(p[1] for p in rp)
        n = len(rp)
        k = int(math.floor(ymin / spacing))
        guard = 0
        while k * spacing < ymax and guard < 5000:
            y = k * spacing + spacing * 0.5
            k += 1
            guard += 1
            xs = []
            for i in range(n):
                x1, y1 = rp[i]
                x2, y2 = rp[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    t = (y - y1) / (y2 - y1)
                    xs.append(x1 + t * (x2 - x1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa, xb = xs[i], xs[i + 1]
                if xb - xa < 1e-6:
                    continue
                self.line((xa * ca - y * sa, xa * sa + y * ca),
                          (xb * ca - y * sa, xb * sa + y * ca), 'hatch', track=False)

    # ---- 文字 ------------------------------------------------------------
    def text(self, x, y, s, fs=FS_DIM, ha='center', va='center', rot=0.0,
             color='k', box=False, weight='normal', track=True):
        kw = {}
        if box:
            kw['bbox'] = dict(boxstyle='square,pad=0.14', fc='white', ec='none')
        self.ax.text(x, y, s, fontsize=fs, ha=ha, va=va, rotation=rot,
                     color=color, fontweight=weight, zorder=8, **kw)
        if track:
            nh = 0.0
            for ch in s:
                nh += 1.0 if ord(ch) > 0x2000 else 0.58
            w = nh * fs / 72.0 / self.upp
            h = fs * 1.3 / 72.0 / self.upp
            if rot:
                w, h = max(w, h), max(w, h)
            self.track(x - w / 2, y - h / 2)
            self.track(x + w / 2, y + h / 2)

    # ---- 箭头 ------------------------------------------------------------
    def arrow(self, p_from, p_to, style='-|>', ms=9.0, lw=0.6, color='k'):
        self.ax.annotate('', xy=p_to, xytext=p_from,
                         arrowprops=dict(arrowstyle=style, mutation_scale=ms,
                                         lw=lw, color=color, shrinkA=0, shrinkB=0,
                                         joinstyle='miter', capstyle='butt'),
                         zorder=6)
        self.track_pts([p_from, p_to])

    # ---- 尺寸标注 --------------------------------------------------------
    def _dt(self, x, y, s, rot=0.0, fs=None):
        self.ax.text(x, y, s, fontsize=(fs or FS_DIM), ha='center', va='center',
                     rotation=rot, color='k', zorder=9,
                     bbox=dict(boxstyle='square,pad=0.12', fc='white', ec='none'))
        self.text(x, y, s, fs=(fs or FS_DIM), rot=rot, ha='center', va='center')

    def hdim(self, x1, x2, y, label, ya=None, yb=None, fs=None,
             over=2.4, gap=1.4, arrow='in', tside='above'):
        s1 = 0.0 if ya is None else math.copysign(1.0, y - ya)
        s2 = 0.0 if yb is None else math.copysign(1.0, y - yb)
        if ya is not None and abs(y - ya) > 1e-9:
            self.line((x1, ya + s1 * gap), (x1, y + s1 * over), 'ext')
        if yb is not None and abs(y - yb) > 1e-9:
            self.line((x2, yb + s2 * gap), (x2, y + s2 * over), 'ext')
        if arrow == 'in':
            self.line((x1, y), (x2, y), 'dim')
            self.arrow((x1, y), (x2, y), '<|-|>')
        else:
            o = 7.0 * self.upp
            self.line((x1 - o, y), (x2 + o, y), 'dim')
            self.arrow((x1 - o, y), (x1, y), '-|>')
            self.arrow((x2 + o, y), (x2, y), '-|>')
        tx = (x1 + x2) / 2.0
        ty = y + (3.4 * self.upp if tside == 'above' else -3.4 * self.upp)
        self._dt(tx, ty, label, 0.0, fs)

    def vdim(self, y1, y2, x, label, xa=None, xb=None, fs=None,
             over=2.4, gap=1.4, arrow='in', side='left'):
        s1 = 0.0 if xa is None else math.copysign(1.0, x - xa)
        s2 = 0.0 if xb is None else math.copysign(1.0, x - xb)
        if xa is not None and abs(x - xa) > 1e-9:
            self.line((xa + s1 * gap, y1), (x + s1 * over, y1), 'ext')
        if xb is not None and abs(x - xb) > 1e-9:
            self.line((xb + s2 * gap, y2), (x + s2 * over, y2), 'ext')
        if arrow == 'in':
            self.line((x, y1), (x, y2), 'dim')
            self.arrow((x, y1), (x, y2), '<|-|>')
        else:
            o = 7.0 * self.upp
            self.line((x, y1 - o), (x, y2 + o), 'dim')
            self.arrow((x, y1 - o), (x, y1), '-|>')
            self.arrow((x, y2 + o), (x, y2), '-|>')
        ty = (y1 + y2) / 2.0
        tx = x - 3.4 * self.upp if side == 'left' else x + 3.4 * self.upp
        self._dt(tx, ty, label, 90.0, fs)

    def ldim(self, p1, p2, off, label, fs=None, over=2.4, gap=1.4, tside=1):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        q1 = (p1[0] + nx * off, p1[1] + ny * off)
        q2 = (p2[0] + nx * off, p2[1] + ny * off)
        self.line((p1[0] + nx * gap, p1[1] + ny * gap),
                  (q1[0] + nx * over, q1[1] + ny * over), 'ext')
        self.line((p2[0] + nx * gap, p2[1] + ny * gap),
                  (q2[0] + nx * over, q2[1] + ny * over), 'ext')
        self.line(q1, q2, 'dim')
        self.arrow(q1, q2, '<|-|>')
        ang = math.degrees(math.atan2(dy, dx)) % 180.0
        rot = ang - 180.0 if ang > 90.0 else ang
        a = math.radians(rot)
        toff = 3.4 * self.upp * tside
        tm = ((q1[0] + q2[0]) / 2.0, (q1[1] + q2[1]) / 2.0)
        self._dt(tm[0] - math.sin(a) * toff, tm[1] + math.cos(a) * toff, label, rot, fs)

    def angdim(self, v, p1, p2, r, label, fs=None):
        a1 = math.degrees(math.atan2(p1[1] - v[1], p1[0] - v[0]))
        a2 = math.degrees(math.atan2(p2[1] - v[1], p2[0] - v[0]))
        d = (a2 - a1) % 360.0
        if d > 180.0:
            a1, a2 = a2, a1
            d = 360.0 - d
        self.arc(v, r, a1, a2, 'dim')
        e = 3.0 * self.upp
        for aa in (a1, a2):
            self.line((v[0] + r * math.cos(math.radians(aa)), v[1] + r * math.sin(math.radians(aa))),
                      (v[0] + (r + e) * math.cos(math.radians(aa)),
                       v[1] + (r + e) * math.sin(math.radians(aa))), 'dim')
        for aa, sgn in ((a1, -1), (a2, 1)):
            t = math.radians(aa + sgn * 7.0)
            self.arrow((v[0] + r * math.cos(t), v[1] + r * math.sin(t)),
                       (v[0] + r * math.cos(math.radians(aa)),
                        v[1] + r * math.sin(math.radians(aa))), '-|>')
        am = math.radians(a1 + (a2 - a1) / 2.0)
        rr = r + 5.5 * self.upp
        self._dt(v[0] + rr * math.cos(am), v[1] + rr * math.sin(am), label, 0.0, fs)

    def leader(self, pt, tail, label, fs=None, tail_len=None, ha=None):
        if tail_len is None:
            tail_len = 5.0 * self.upp
        dirx = 1.0 if tail[0] >= pt[0] else -1.0
        end = (tail[0] + dirx * tail_len, tail[1])
        self.line(tail, end, 'dim')
        self.line(pt, tail, 'dim')
        self.arrow(tail, pt, '-|>')
        if ha is None:
            ha = 'left' if dirx > 0 else 'right'
        tx = end[0] + (1.0 * self.upp if dirx > 0 else -1.0 * self.upp)
        self.text(tx, end[1], label, fs or FS_DIM, ha=ha, va='center', box=True)


# --------------------------------------------------------------------------
# 2. 页面骨架
# --------------------------------------------------------------------------
BORDER = 0.0255
RECT_DRAW = [0.056, 0.150, 0.888, 0.728]
TITLE_BLOCK = [0.668, 0.040, 0.3065, 0.090]


def page_frame(fig, title, subtitle, foot1, foot2, page_label, scale_note='1:1'):
    fig.add_artist(Rectangle((BORDER, BORDER), 1 - 2 * BORDER, 1 - 2 * BORDER,
                             fill=False, ec='#000000', lw=1.7, transform=fig.transFigure))
    fig.add_artist(Rectangle((BORDER + 0.0035, BORDER + 0.0035),
                             1 - 2 * BORDER - 0.007, 1 - 2 * BORDER - 0.007,
                             fill=False, ec='#000000', lw=0.55, transform=fig.transFigure))
    fig.text(0.056, 0.946, title, fontsize=15.5, fontweight='bold',
             ha='left', va='center', color='#000000')
    fig.text(0.056, 0.9065, subtitle, fontsize=9.6, ha='left', va='center', color='#303030')
    fig.add_artist(plt.Line2D([0.056, 0.944], [0.1385, 0.1385], color='#000000',
                              lw=0.8, transform=fig.transFigure))
    bx, by, bw, bh = TITLE_BLOCK
    fig.add_artist(Rectangle((bx, by), bw, bh, fill=False, ec='#000000', lw=0.9,
                             transform=fig.transFigure))
    fig.add_artist(plt.Line2D([bx, bx + bw], [by + bh * 2 / 3.0, by + bh * 2 / 3.0],
                              color='#000000', lw=0.5, transform=fig.transFigure))
    fig.add_artist(plt.Line2D([bx, bx + bw], [by + bh / 3.0, by + bh / 3.0],
                              color='#000000', lw=0.5, transform=fig.transFigure))
    fig.add_artist(plt.Line2D([bx + bw * 0.40, bx + bw * 0.40], [by + bh / 3.0, by + bh],
                              color='#000000', lw=0.5, transform=fig.transFigure))
    fig.text(bx + 0.006, by + bh * 5 / 6.0, '图名  ' + page_label, fontsize=7.2,
             ha='left', va='center')
    fig.text(bx + 0.006, by + bh / 2.0, '比例  ' + scale_note, fontsize=7.2,
             ha='left', va='center')
    fig.text(bx + bw * 0.40 + 0.006, by + bh / 2.0, '投影法  第一角（GB）', fontsize=7.2,
             ha='left', va='center')
    fig.text(bx + 0.006, by + bh / 6.0, '单位  mm（数字后不写单位）', fontsize=7.2,
             ha='left', va='center')
    fig.text(bx + bw * 0.40 + 0.006, by + bh / 6.0, '零基础练习图纸 · 建模用', fontsize=7.2,
             ha='left', va='center')
    fig.text(0.056, 0.1055, foot1, fontsize=8.3, ha='left', va='center')
    fig.text(0.056, 0.0675, foot2, fontsize=8.3, ha='left', va='center')


def new_fig():
    return plt.figure(figsize=(A4W, A4H), dpi=110)


def build_page(draw_fn, title, subtitle, foot1, foot2, page_label, scale_note='1:1'):
    upp = 0.25
    sheet = None
    for _ in range(2):
        fig = new_fig()
        page_frame(fig, title, subtitle, foot1, foot2, page_label, scale_note)
        sheet = Sheet(fig, RECT_DRAW, upp=upp)
        draw_fn(sheet)
        sheet.fit(pad=6.0)
        if _ == 0:
            upp = sheet.upp
            plt.close(fig)
    return sheet.fig

# ==========================================================================
# 第一部分：草图练习
# ==========================================================================
def p01(s):
    """练习01 对称底板（草图）"""
    # 轮廓：100×60 中心矩形，四角 R8
    R = 8.0
    x0, x1, y0, y1 = -50.0, 50.0, -30.0, 30.0
    path = [(-42, -30), (42, -30)]
    s.polyline(path, 'out', track=False)
    s.arc((42, -22), R, -90, 0)
    s.line((50, -22), (50, 22))
    s.arc((42, 22), R, 0, 90)
    s.line((42, 30), (-42, 30))
    s.arc((-42, 22), R, 90, 180)
    s.line((-50, 22), (-50, -22))
    s.arc((-42, -22), R, 180, 270)
    s.line((-50, -22), (-50, -21))          # 闭合段（与起点重合）
    # 中心线
    s.cline((-58, 0), (58, 0))
    s.cline((0, -38), (0, 38))
    # 孔
    s.circle((0, 0), 15.0)
    for cx in (-38, 38):
        for cy in (-18, 18):
            s.circle((cx, cy), 4.5)
            s.center_cross((cx, cy), 4.5)
    # 尺寸
    s.hdim(38, -38, -38, '76', ya=-18, yb=-18)
    s.hdim(50, -50, -50, '100', ya=-30, yb=-30)
    s.vdim(-30, 30, -64, '60', xa=-50, xb=-50)
    s.vdim(-18, 18, 62, '36', xa=38, xb=38)
    s.leader((-47.66, 27.66), (-66, 38), 'R8')
    s.leader((41.2, 21.2), (66, 34), '4×φ9')
    s.leader((10.61, -10.61), (58, -40), 'φ30')
    s.text(0, -60, '孔心距相邻两外边缘 12（由 76、36 算出，不再重复标注）',
           FS_NOTE, ha='center', va='center')


def p02(s):
    """练习02 角度支架轮廓（草图）"""
    R = 8.0
    pts = []
    pts.append((8, 80))                     # 左上圆角切点
    pts.append((40, 80))
    pts.append((80, 40))
    pts.append((112, 40))                   # 右下圆角切点
    pts += s.arc((112, 32), R, 90, 0)       # 右下 R8
    pts.append((120, 0))
    pts.append((0, 0))
    pts.append((0, 72))
    pts += s.arc((8, 72), R, 180, 90)       # 左上 R8
    s.polyline(pts, 'out', closed=True, track=True)
    # 中心线（孔）
    s.cline((38, 20), (82, 20))
    s.cline((60, -6), (60, 46))
    s.circle((60, 20), 10.0)
    # 尺寸
    # φ20 孔定位（缺这两个尺寸，草图永远无法完全定义）
    s.hdim(0, 60, -14, '60', ya=0, yb=20)
    s.vdim(0, 20, 134, '20', xa=120, xb=60)
    s.hdim(0, 120, -30, '120', ya=0, yb=0)
    s.vdim(0, 80, -14, '80', xa=0, xb=0)
    s.hdim(0, 40, 94, '40', ya=80, yb=80)
    s.vdim(0, 40, 152, '40', xa=120, xb=110)
    s.line((80, 40), (50, 40), 'ext')
    s.angdim((80, 40), (40, 40), (40, 80), 26, '45°')
    s.leader((2.34, 77.66), (-20, 98), 'R8')
    s.leader((117.66, 37.66), (132, 28), 'R8')
    s.leader((52.93, 27.07), (30, 44), 'φ20')


def p03(s):
    """练习03 连杆轮廓（草图）"""
    C1, R1 = (-45.0, 0.0), 25.0
    C2, R2 = (45.0, 0.0), 22.0
    d = 90.0
    al = math.degrees(math.asin((R1 - R2) / d))
    a_up, a_dn = 90.0 + al, 270.0 - al
    p1u = (C1[0] + R1 * math.cos(math.radians(a_up)), C1[1] + R1 * math.sin(math.radians(a_up)))
    p1d = (C1[0] + R1 * math.cos(math.radians(a_dn)), C1[1] + R1 * math.sin(math.radians(a_dn)))
    p2u = (C2[0] + R2 * math.cos(math.radians(a_up)), C2[1] + R2 * math.sin(math.radians(a_up)))
    p2d = (C2[0] + R2 * math.cos(math.radians(a_dn)), C2[1] + R2 * math.sin(math.radians(a_dn)))
    pts = s.arc(C1, R1, a_up, a_dn)
    pts.append(p1d)
    pts.append(p2d)
    pts += s.arc(C2, R2, a_dn, a_up + 360.0)
    pts.append(p2u)
    pts.append(p1u)
    s.polyline(pts, 'out', closed=True, track=True)
    # 中心线
    s.cline((-72, 0), (72, 0))
    s.center_cross((C1[0], 0), 8.0)
    s.center_cross((C2[0], 0), 8.0)
    # 孔
    s.circle(C1, 7.5)
    s.circle(C2, 6.0)
    # 尺寸
    s.hdim(-45, 45, -42, '90', ya=0, yb=0)
    s.leader((-64.15, 16.07), (-84, 30), 'R25')
    s.leader((61.85, 14.14), (82, 30), 'R22')
    s.leader((-51.11, -4.30), (-72, -22), 'φ15')
    s.leader((49.91, -3.44), (70, -22), 'φ12')


def p04(s):
    """练习04 腰形槽板（草图）"""
    R = 10.0
    x0, x1, y0, y1 = -70.0, 70.0, -35.0, 35.0
    s.polyline([(-60, -35), (60, -35)], 'out', track=False)
    s.arc((60, -25), R, -90, 0)
    s.line((70, -25), (70, 25))
    s.arc((60, 25), R, 0, 90)
    s.line((60, 35), (-60, 35))
    s.arc((-60, 25), R, 90, 180)
    s.line((-70, 25), (-70, -25))
    s.arc((-60, -25), R, 180, 270)
    # 腰形槽
    s.line((-30, 10), (30, 10))
    s.line((30, -10), (-30, -10))
    s.arc((30, 0), 10.0, 90, -90)
    s.arc((-30, 0), 10.0, 270, 90)
    # 中心线
    s.cline((-80, 0), (80, 0))
    s.cline((0, -44), (0, 44))
    # 孔
    for cx in (-60, 60):
        for cy in (-25, 25):
            s.circle((cx, cy), 4.0)
            s.center_cross((cx, cy), 4.0)
    # 尺寸
    s.hdim(-30, 30, -20, '60', ya=-10, yb=-10, tside='below')
    s.vdim(-10, 10, -54, '20', xa=-30, xb=-30)
    s.hdim(60, -60, -64, '120', ya=-25, yb=-25)
    s.hdim(70, -70, -50, '140', ya=-35, yb=-35)
    s.vdim(-35, 35, -86, '70', xa=-70, xb=-70)
    s.vdim(-25, 25, 86, '50', xa=60, xb=60)
    s.leader((67.07, 32.07), (84, 40), 'R10')
    s.leader((-63.2, 21.2), (-84, 42), '4×φ8')


def p05(s):
    """练习05 减重连杆板（草图）"""
    R = 45.0
    C1, C2 = (-60.0, 0.0), (60.0, 0.0)
    pts = s.arc(C1, R, 90, 270)
    pts.append((-60, -45))
    pts.append((60, -45))
    pts += s.arc(C2, R, 270, 450)
    pts.append((60, 45))
    pts.append((-60, 45))
    s.polyline(pts, 'out', closed=True, track=True)
    # 椭圆减重孔
    s.ellipse((0, 0), 60.0, 25.0)
    # 中心线
    s.cline((-112, 0), (112, 0))
    s.cline((0, -52), (0, 52))
    s.center_cross(C1, 4.0)
    s.center_cross(C2, 4.0)
    # 2×φ12
    for cx in (-75, 75):
        s.circle((cx, 0), 6.0)
        s.center_cross((cx, 0), 6.0)
    # 尺寸
    s.hdim(-60, 60, -60, '120', ya=0, yb=0)
    s.hdim(-75, 75, -76, '150', ya=0, yb=0)
    s.hdim(-105, 105, -92, '(210)', ya=0, yb=0)
    s.vdim(-45, 45, -92, '(90)', xa=-60, xb=-60)
    s.leader((-102.31, 15.39), (-120, 30), '2×R45')
    s.leader((79.24, 4.24), (96, 22), '2×φ12')
    s.line((0, 25), (0, 36), 'dim')
    s.arrow((0, 33), (0, 25), '-|>')
    s.text(0, 39, '椭圆 120×50', FS_DIM, ha='center', va='center', box=True)
    s.text(0, -104, '括号尺寸为参考尺寸（由 120、R45 算出），建模时不必标注',
           FS_NOTE, ha='center', va='center')


# ==========================================================================
# 第三部分：封面与主流程
# ==========================================================================
def build_cover():
    fig = plt.figure(figsize=(A4W, A4H), dpi=110)
    fig.add_artist(Rectangle((BORDER, BORDER), 1 - 2 * BORDER, 1 - 2 * BORDER,
                             fill=False, ec='#000000', lw=1.7, transform=fig.transFigure))
    fig.add_artist(Rectangle((BORDER + 0.0035, BORDER + 0.0035),
                             1 - 2 * BORDER - 0.007, 1 - 2 * BORDER - 0.007,
                             fill=False, ec='#000000', lw=0.55, transform=fig.transFigure))
    fig.text(0.5, 0.905, 'SolidWorks 零基础练习图纸', fontsize=25,
             ha='center', va='center')
    fig.text(0.5, 0.850, '10 个渐进练习   ·   草图 5 个 + 零件 5 个',
             fontsize=13, ha='center', va='center', color='#555555')
    fig.text(0.5, 0.806, '第一角投影（GB）    |    单位 mm    |    括号尺寸 = 参考尺寸',
             fontsize=10.5, ha='center', va='center', color='#777777')
    fig.add_artist(plt.Line2D([0.16, 0.84], [0.768, 0.768], color='#000000',
                              lw=0.8, transform=fig.transFigure))

    col1 = (
        "怎么用这套图纸\n"
        "  1  按图纸把形状建出来，不要先看答案。\n"
        "  2  草图练习：确认状态栏显示「完全定义」，图形全黑。\n"
        "  3  零件练习：先在纸上写下特征顺序，再打开软件。\n"
        "  4  做完做「改图测试」：把主尺寸改掉再改回来，看模型\n"
        "      会不会报错。报错就是思路有问题，回图纸重看，\n"
        "      不要硬修模型。\n"
        "\n"
        "三个通用自检动作（每题都做）\n"
        "  ① 状态栏必须显示「完全定义」，图形全黑。还有蓝色\n"
        "      元素就说明缺约束：拖一下它，看它往哪动。\n"
        "  ② 特征树从下往上读，每一行都要能说出它为什么存在。\n"
        "  ③ 改图测试：改主尺寸 → Ctrl+B → 应合理变形且特征树\n"
        "      无红色/黄色 → 再改回原值。"
    )
    col2 = (
        "这套图纸的三个刻意设计\n"
        "  · 尺寸不写单位：工程图惯例，单位在标题栏统一声明。\n"
        "  · 不封闭尺寸链：不重复标注能由其它尺寸推出的值。\n"
        "    例如练习 01 已给 100 与 76，孔心到板边的 12 就不再\n"
        "    标；练习 05 的 (210)、(90) 加了括号，表示「参考\n"
        "    尺寸」——只供核对，不作加工依据。\n"
        "  · 每个练习都标了「考核点」：它比形状本身更重要。\n"
        "\n"
        "完成标准\n"
        "  草图练习 —— 草图完全定义（全黑），拖动任何图元都不动。\n"
        "  零件练习 —— 单一有效实体，特征树无红色/黄色报错，\n"
        "              改尺寸能正确重算。\n"
        "\n"
        "投影法提醒（第一角 GB）\n"
        "  俯视图在主视图正下方、左视图在主视图正右方；这两种\n"
        "  视图里「靠近主视图的一侧」对应物体的【后面】。"
    )
    fig.text(0.085, 0.718, col1, fontsize=10.4, va='top', ha='left', linespacing=1.78)
    fig.text(0.520, 0.718, col2, fontsize=10.4, va='top', ha='left', linespacing=1.78)
    fig.text(0.5, 0.072,
             '配套：E:\\SW\\02-学习路线\\零基础学习路线图.md   ·   '
             'E:\\SW\\03-练习图纸\\答案与建模思路.md',
             fontsize=9.5, ha='center', va='center', color='#777777')
    return fig


PAGE_DEFS = [
    (p01, '练习 01 · 对称底板（草图）',
     '考核点：中心矩形 + 对称约束 + 镜像    |    单位：mm    |    第一角投影',
     '本练习重点：中心线打底 → 只画一半 → 用【镜像实体】。不要左右各画一遍，也不要用尺寸堆出对称。',
     '完成标准：草图完全定义（全黑）。图中只标 100、60、76、36；孔到板边的 12 是算出来的，故意不标（避免封闭尺寸链）。',
     '练习01 对称底板', '练习01'),

    (p02, '练习 02 · 角度支架轮廓（草图）',
     '考核点：角度尺寸 + 几何关系优先级    |    单位：mm    |    第一角投影',
     '本练习重点：斜边用「与水平成 45°」表达，不要靠坐标硬凑；R8 圆角改变相邻边的标注基准，注意圆角与边的关系。',
     '完成标准：草图完全定义（全黑）。60、20 是 φ20 孔的位置尺寸——缺了它们草图永远无法完全定义。检查：把 45° 改成 60°，轮廓应正确变形且不报错。',
     '练习02 角度支架轮廓', '练习02'),

    (p03, '练习 03 · 连杆轮廓（草图）',
     '考核点：相切约束 + 同心    |    单位：mm    |    第一角投影',
     '本练习重点：外轮廓用「两圆 + 外公切线」构造，切点由相切关系自动确定，不要手动画近似直线。两孔与各自外圆同心。',
     '完成标准：草图完全定义（全黑）。注意 R25≠R22，所以外公切线不平行于中心线（夹角约 1.9°）——这正是必须用相切约束的原因。把 90 改成 110，外形应保持相切且不报错。',
     '练习03 连杆轮廓', '练习03'),

    (p04, '练习 04 · 腰形槽板（草图）',
     '考核点：直槽口工具 + 镜像    |    单位：mm    |    第一角投影',
     '本练习重点：腰形槽用【直槽口】工具一次画出，不要用两圆弧加两直线拼；4 个孔是矩形布置，用【镜像】两次或【线性草图阵列】2×2。',
     '完成标准：草图完全定义（全黑）。注意：4 个孔不在圆周上，用【圆周草图阵列】是做不出来的——这是本练习专门埋的坑。',
     '练习04 腰形槽板', '练习04'),

    (p05, '练习 05 · 减重连杆板（草图）',
     '考核点：相切 + 椭圆 + 对称    |    单位：mm    |    第一角投影',
     '本练习重点：两端等半径圆的外公切线是水平的，用相切关系约束；椭圆孔用【椭圆】工具，长轴短轴都要与中心线建立关系。',
     '完成标准：草图完全定义（全黑）。带括号的 (210)、(90) 是参考尺寸——由 120 和 R45 确定，只供核对，不作加工依据（标出来就是让你看见什么叫封闭尺寸链）。',
     '练习05 减重连杆板', '练习05'),

    (p06, '练习 06 · L 型支架（零件）',
     '考核点：拉伸 + 筋 + 基准面选择    |    单位：mm    |    第一角投影（俯视图在正下方，左视图在正右方）',
     '本练习重点：先底板 → 再立板 → 再加强筋 → 最后打孔。注意：加强筋是三角筋，在主视图和俯视图里都投影成矩形，',
     '必须看左视图才能看出它是三角形的——这就是为什么要三视图。第一角约定：俯视图与左视图靠近主视图的一侧对应物体的【后面】。',
     '练习06 L 型支架', '练习06'),

    (p07, '练习 07 · 法兰盘（零件）',
     '考核点：旋转 + 圆周阵列 + 倒角    |    单位：mm    |    第一角投影',
     '本练习重点：回转体优先用【旋转凸台】而不是拉伸；6 个螺栓孔用【圆周阵列】一次生成，不要画 6 次；倒角放最后。',
     '完成标准：单一有效实体；6 孔 PCD φ90 均匀分布（60°）；两侧倒角对称。改 φ120 为 φ140，外径变大而 PCD 与孔位不变。',
     '练习07 法兰盘', '练习07'),

    (p08, '练习 08 · 阶梯轴（零件）',
     '考核点：旋转 + 倒角 + 退刀槽 + 键槽    |    单位：mm    |    第一角投影',
     '本练习重点：轴类零件一律用【旋转凸台】，草图画一半剖面并绕中心线旋转；键槽用【拉伸切除】+ 基准面；退刀槽在轴肩的小直径一侧。',
     '完成标准：单一有效实体；分段长度逐个按图。(150) 是参考尺寸（=40+50+40+20），只供核对——分段长度才是加工依据。',
     '练习08 阶梯轴', '练习08'),

    (p09, '练习 09 · 减重带轮（零件）',
     '考核点：旋转体 + 减重孔阵列 + 倒角    |    单位：mm    |    第一角投影',
     '本练习重点：轮缘、轮毂、中心孔一次旋转成型最省事；4 个减重孔用【圆周阵列】；键槽宽度与深度按标准查表，不要自定。',
     '完成标准：单一有效实体；两侧轮毂对称凸出；减重孔 90° 均布。注意键槽深 2.5 是从【孔壁】算起，不是从轴心算。',
     '练习09 减重带轮', '练习09'),

    (p10, '练习 10 · 轴承座（零件）',
     '考核点：综合件 —— 拉伸 + 旋转 + 孔 + 圆角    |    单位：mm    |    第一角投影',
     '本练习重点：建议顺序 底板 → 支撑板 → 顶部回转体 → 轴承孔 → 安装孔 → 最后加 R3 圆角。回转体轴线沿 Y（主视图里它是圆）。',
     '完成标准：单一有效实体；轴承孔轴线与顶部回转体同轴。改 45 这个高度，孔与顶部回转体应一起移动（支撑板高度 33 是推出来的）。',
     '练习10 轴承座', '练习10'),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    prev = os.path.join(here, 'preview')
    os.makedirs(prev, exist_ok=True)
    pdf_path = os.path.join(here, 'SolidWorks-练习图纸.pdf')

    with PdfPages(pdf_path) as pdf:
        fig = build_cover()
        pdf.savefig(fig)
        fig.savefig(os.path.join(prev, '封面.png'), dpi=150)
        plt.close(fig)
        print('OK  封面')

        for fn, title, sub, f1, f2, label, png in PAGE_DEFS:
            fig = build_page(fn, title, sub, f1, f2, label)
            pdf.savefig(fig)
            fig.savefig(os.path.join(prev, png + '.png'), dpi=150)
            plt.close(fig)
            print('OK ', png)

    print('PDF ->', pdf_path)


if __name__ == '__main__':
    main()
