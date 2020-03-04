import numpy as np
import nanogui.nanovg as nvg

class DraggableKnob:
    def __init__(self, p=[0,0]):
        self.p = np.array(p)

        self.hover = False
        self.drag_possible = False

        self.directional = False
        self.angle = 0

        self.active = True

    def update(self, input):
        if not self.active:
            return

        d = input.scale*0.03
        dist_current2 = (input.mouse_p[0] - self.p[0])**2 + (input.mouse_p[1] - self.p[1])**2
        dist_last2    = (input.mouse_p_click[0] - self.p[0])**2 + (input.mouse_p_click[1] - self.p[1])**2
        self.hover = False
        self.drag_possible = False
        if (dist_current2 < d**2):
            self.hover = True
            if not dist_last2 > d**2:
                self.drag_possible = True

    def draw(self, ctx, scale=1.0):
        if not self.active:
            return

        if self.directional:
            if self.hover:
                ctx.StrokeColor(nvg.RGB(255, 0, 0))
                ctx.FillColor(nvg.RGB(255, 0, 0))
            else:
                ctx.StrokeColor(nvg.RGB(255, 255, 255))
                ctx.FillColor(nvg.RGB(255, 255, 255))
            p0 = self.p
            theta = np.radians(self.angle)
            wo = np.array([np.cos(theta), np.sin(theta)])
            p1 = p0 + wo * 0.1*scale

            ctx.StrokeWidth(0.012*scale)
            ctx.BeginPath()
            ctx.MoveTo(p0[0], p0[1])
            ctx.LineTo(p1[0], p1[1])
            ctx.Stroke()

            wo2 = np.array([np.cos(theta+0.3), np.sin(theta+0.3)])
            wo3 = np.array([np.cos(theta-0.3), np.sin(theta-0.3)])

            p2 = p0 + wo2 * 0.1*scale
            p3 = p0 + wo3 * 0.1*scale
            p4 = p1 + wo  * 0.05*scale

            ctx.BeginPath()
            ctx.MoveTo(p4[0], p4[1])
            ctx.LineTo(p2[0], p2[1])
            ctx.LineTo(p3[0], p3[1])
            ctx.LineTo(p4[0], p4[1])
            ctx.Fill()

        if self.hover:
            ctx.FillColor(nvg.RGB(255, 0, 0))
        else:
            ctx.FillColor(nvg.RGB(255, 255, 255))


        ctx.StrokeColor(nvg.RGB(0, 0, 0))

        ctx.StrokeWidth(0.01*scale)

        ctx.BeginPath()
        ctx.Circle(self.p[0], self.p[1], 0.022*scale)
        ctx.Fill()
        ctx.Stroke()
