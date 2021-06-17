from misc import *
from manifolds import *

class Path():
    def __init__(self):
        self.vertices = []
        self.n_total = 0
        self.n_specular = 0
        self.singular = False

    def __getitem__(self, i):
        return self.vertices[i]

    def __setitem__(self, key, val):
        self.vertices[key] = val

    def __len__(self):
        return len(self.vertices)

    def append(self, vtx):
        vtx.C = 0
        vtx.dC_du_prev = 0
        vtx.dC_du_cur  = 0
        vtx.dC_du_next = 0
        vtx.dM_dz  = 0
        vtx.dM_de  = 0
        self.vertices.append(vtx)
        if vtx.shape.type == Shape.Type.Reflection or vtx.shape.type == Shape.Type.Refraction:
            self.n_specular += 1
        self.n_total += 1

    def copy(self):
        path = Path()

        for i in range(len(self)):
            vtx = self[i].copy()
            path.append(vtx)
        return path

    def copy_positions(self):
        positions = []
        for i in range(len(self)):
            positions.append(copy.copy(self[i].p))
        return positions

    def __repr__(self):
        ret = "Path vertices: %d (%d specular)\n\n" % (self.n_total, self.n_specular)
        for i in range(len(self)):
            vtx = self.vertices[i]

            p = np.array2string(vtx.p, formatter={'float_kind':lambda x: "%.2f" % x})
            n = np.array2string(vtx.n, formatter={'float_kind':lambda x: "%.2f" % x})
            dp_du = np.array2string(vtx.dp_du, formatter={'float_kind':lambda x: "%.2f" % x})
            dn_du = np.array2string(vtx.dn_du, formatter={'float_kind':lambda x: "%.2f" % x})
            bsdf = vtx.shape.type
            bsdf_str = "S" if bsdf == Shape.Type.Reflection or bsdf == Shape.Type.Refraction else "D"
            bsdf_str += ", " + vtx.shape.name
            ret += "%d (%s):\n\tp: %s,     dp_du: %s\n\tn: %s,     dn_du: %s\n" % (i, bsdf_str, p, dp_du, n, dn_du)

        return ret

    def has_specular_segment(self):
        K = len(self)
        if K < 3:
            return False

        test = True
        for k, vtx in enumerate(self.vertices):
            if k == 0 or k == K-1:
                test &= (vtx.shape.type == Shape.Type.Diffuse or
                         vtx.shape.type == Shape.Type.Emitter)
            else:
                test &= (vtx.shape.type == Shape.Type.Reflection or
                         vtx.shape.type == Shape.Type.Refraction)
        return test

    def grad_constraints_halfvector(self, k):
        C = np.inf
        dC = [0, 0, 0]

        x_prev = self.vertices[k-1].p
        x_cur  = self.vertices[k].p
        x_next = self.vertices[k+1].p

        wo = x_next - x_cur
        wi = x_prev - x_cur
        ilo = norm(wo)
        ili = norm(wi)
        if ilo == 0.0 or ili == 0.0:
            return False, C, dC
        ilo = 1.0 / ilo
        ili = 1.0 / ili
        wo *= ilo
        wi *= ili

        eta = self.vertices[k].eta
        if dot(wi, self.vertices[k].n) < 0.0:
            eta = 1.0/eta
        h = wi + eta * wo
        if eta != 1.0:
            h *= -1
        ilh = 1.0 / norm(h)
        h *= ilh

        # For debugging only (see "print_derivative_debug")
        self.vertices[k].h = h

        ilo *= eta * ilh
        ili *= ilh

        # Derivative of specular constraint w.r.t. u_{i-1}
        dh_du = ili * (self.vertices[k-1].dp_du - wi*dot(wi, self.vertices[k-1].dp_du))
        dh_du -= h*dot(dh_du, h)
        if eta != 1.0:
            dh_du *= -1
        dC_du_prev = dot(self.vertices[k].s, dh_du)
        self.vertices[k].dh_du_prev = dh_du

        # Derivative of specular constraint w.r.t. u_{i}
        dh_du = -self.vertices[k].dp_du * (ili + ilo) + wi * (dot(wi, self.vertices[k].dp_du) * ili) \
                                                      + wo * (dot(wo, self.vertices[k].dp_du) * ilo)
        dh_du -= h*dot(dh_du, h)
        if eta != 1.0:
            dh_du *= -1
        dC_du_cur = dot(self.vertices[k].ds_du, h) + dot(self.vertices[k].s, dh_du)
        self.vertices[k].dh_du_cur = dh_du

        # Derivative of specular constraint w.r.t. u_{i+1}
        dh_du = ilo * (self.vertices[k+1].dp_du - wo*dot(wo, self.vertices[k+1].dp_du))
        dh_du -= h*dot(dh_du, h)
        if eta != 1.0:
            dh_du *= -1
        dC_du_next = dot(self.vertices[k].s, dh_du)
        self.vertices[k].dh_du_next = dh_du

        # Evaluation of specular constraint
        H = dot(self.vertices[k].s, h)
        m = self.vertices[k].s * self.vertices[k].n_offset[0] + self.vertices[k].n * self.vertices[k].n_offset[1]
        N = dot(self.vertices[k].s, m)
        C = H - N

        dC = [dC_du_prev, dC_du_cur, dC_du_next]
        return True, C, dC

    def grad_constraints_anglediff(self, k):
        C = np.inf
        dC = [0, 0, 0]

        x_prev = self.vertices[k-1].p
        x_cur  = self.vertices[k].p
        x_next = self.vertices[k+1].p

        wo = x_next - x_cur
        wi = x_prev - x_cur
        ilo = norm(wo)
        ili = norm(wi)
        if ilo == 0.0 or ili == 0.0:
            return False, C, dC
        ilo = 1.0 / ilo
        ili = 1.0 / ili
        wo *= ilo
        wi *= ili

        dwo_du_cur = -ilo * (self.vertices[k].dp_du - wo*dot(wo, self.vertices[k].dp_du))
        dwi_du_cur = -ili * (self.vertices[k].dp_du - wi*dot(wi, self.vertices[k].dp_du))

        # For debugging only (see "print_derivative_debug")
        self.vertices[k].wo = wo
        self.vertices[k].wi = wi
        self.vertices[k].dwo_du_prev = np.array([0, 0])
        self.vertices[k].dwo_du_cur  = dwo_du_cur
        self.vertices[k].dwo_du_next = np.array([0, 0])
        self.vertices[k].dwi_du_prev = np.array([0, 0])
        self.vertices[k].dwi_du_cur  = dwi_du_cur
        self.vertices[k].dwi_du_next = np.array([0, 0])
        self.vertices[k].wio = np.array([0, 0])
        self.vertices[k].woi = np.array([0, 0])
        self.vertices[k].dwio_du_prev = np.array([0, 0])
        self.vertices[k].dwio_du_cur  = np.array([0, 0])
        self.vertices[k].dwio_du_next = np.array([0, 0])
        self.vertices[k].dwoi_du_prev = np.array([0, 0])
        self.vertices[k].dwoi_du_cur  = np.array([0, 0])
        self.vertices[k].dwoi_du_next = np.array([0, 0])

        self.vertices[k].po = 0
        self.vertices[k].pio = 0
        self.vertices[k].pi = 0
        self.vertices[k].poi = 0
        self.vertices[k].dpo_du_prev= 0
        self.vertices[k].dpio_du_prev = 0
        self.vertices[k].dpi_du_prev = 0
        self.vertices[k].dpoi_du_prev = 0
        self.vertices[k].dpo_du_cur = 0
        self.vertices[k].dpio_du_cur = 0
        self.vertices[k].dpi_du_cur = 0
        self.vertices[k].dpoi_du_cur = 0
        self.vertices[k].dpo_du_next = 0
        self.vertices[k].dpio_du_next = 0
        self.vertices[k].dpi_du_next = 0
        self.vertices[k].dpoi_du_next = 0

        def transform(w, n, eta):
            if eta == 1.0:
                return reflect(w, n)
            else:
                return refract(w, n, eta)

        def d_transform(w, dw_du, n, dn_du, eta):
            if eta == 1.0:
                return d_reflect(w, dw_du, n, dn_du)
            else:
                return d_refract(w, dw_du, n, dn_du, eta)

        # Handle offset normals. These lines are no-ops in the n_offset=[0, 1] case
        n = self.vertices[k].s * self.vertices[k].n_offset[0] + \
            self.vertices[k].n * self.vertices[k].n_offset[1]
        dn_du = self.vertices[k].ds_du * self.vertices[k].n_offset[0] + \
                self.vertices[k].dn_du * self.vertices[k].n_offset[1]

        dC_du_prev = 0
        dC_du_cur  = 0
        dC_du_next = 0

        # Set up constraint function and its derivatives
        valid_refr_i, wio = transform(wi, n, self.vertices[k].eta)
        if valid_refr_i:
            po  = angle(wo)
            pio = angle(wio)
            C = po - dpi
            # Take care of periodicity
            if C < -np.pi:
                C += 2*np.pi
            elif C > np.pi:
                C -= 2*np.pi

            # Derivative of specular constraint w.r.t. u_{i-1}
            dwi_du_prev = ili * (self.vertices[k-1].dp_du - wi*dot(wi, self.vertices[k-1].dp_du))
            # dwo_du_prev = ilo * (self.vertices[k-1].dp_du - wo*dot(wo, self.vertices[k-1].dp_du))  # = 0
            dwio_du_prev = d_transform(wi, dwi_du_prev, n, np.array([0,0]), self.vertices[k].eta)    # Possible optimization: specific implementation here that already knows some of these are 0.
            # dpo_du = d_angle(wo, dwo_du_prev) # = 0
            dpio_du = d_angle(wio, dwio_du_prev)

            dC_du_prev = -dpio_du
            self.vertices[k].dpio_du_prev = dpio_du

            # Derivative of specular constraint w.r.t. u_{i}
            dwio_du_cur = d_transform(wi, dwi_du_cur, n, dn_du, self.vertices[k].eta)
            dpo_du  = d_angle(wo, dwo_du_cur)
            dpio_du = d_angle(wio, dwio_du_cur)

            dC_du_cur = dpo_du - dpio_du
            self.vertices[k].dpo_du_cur = dpo_du
            self.vertices[k].dpio_du_cur = dpio_du

            # Derivative of specular constraint w.r.t. u_{i+1}
            # dwi_du_next = ili * (selv.vertices[k+1].dp_du - wi*dot(wi, self.vertices[k+1].dp_du))  # = 0
            dwo_du_next = ilo * (self.vertices[k+1].dp_du - wo*dot(wo, self.vertices[k+1].dp_du))
            # dwio_du_next = d_transform(wi, dwi_du_next, n, np.array([0,0]), self.vertices[k].eta) # = 0
            dpo_du = d_angle(wo, dwo_du_next)
            # dpio_du = d_angle(wio, dwio_du_next) # = 0

            dC_du_next = dpo_du
            self.vertices[k].dpo_du_next = dpo_du

            self.vertices[k].wio = wio
            self.vertices[k].dwi_du_prev = dwi_du_prev
            self.vertices[k].dwio_du_prev = dwio_du_prev
            self.vertices[k].dwio_du_cur = dwio_du_cur
            self.vertices[k].dwo_du_next = dwo_du_next

            self.vertices[k].po = po
            self.vertices[k].pio = pio

        valid_refr_o, woi = transform(wo, n, self.vertices[k].eta)
        if valid_refr_o and not valid_refr_i:
            pi  = angle(wi)
            poi = angle(woi)
            C = pi - poi

            # Derivative of specular constraint w.r.t. u_{i-1}
            dwi_du_prev = ili * (self.vertices[k-1].dp_du - wi*dot(wi, self.vertices[k-1].dp_du))
            # dwo_du_prev = ilo * (self.vertices[k-1].dp_du - wo*dot(wo, self.vertices[k-1].dp_du)) # = 0
            # dwoi_du_prev = d_transform(wo, dwo_du_prev, n, np.array([0,0]), self.vertices[k].eta) # = 0
            dpi_du = d_angle(wi, dwi_du_prev)
            # dpoi_du = d_angle(woi, dwoi_du_prev) # = 0

            dC_du_prev = dpi_du
            self.vertices[k].dpi_du_prev = dpi_du

            # Derivative of specular constraint w.r.t. u_{i}
            dwoi_du_cur = d_transform(wo, dwo_du_cur, n, dn_du, self.vertices[k].eta)
            dpi_du = d_angle(wi, dwi_du_cur)
            dpoi_du = d_angle(woi, dwoi_du_cur)

            dC_du_cur = dpi_du - dpoi_du
            self.vertices[k].dpi_du_cur = dpi_du
            self.vertices[k].dpoi_du_cur = dpoi_du

            # Derivative of specular constraint w.r.t. u_{i+1}
            # dwi_du_next = ili * (self.vertices[k+1].dp_du - wi*dot(wi, self.vertices[k+1].dp_du))  # = 0
            dwo_du_next = ilo * (self.vertices[k+1].dp_du - wo*dot(wo, self.vertices[k+1].dp_du))
            dwoi_du_next = d_transform(wo, dwo_du_next, n, np.array([0,0]), self.vertices[k].eta);   # Possible optimization: specific implementation here that already knows some of these are 0.

            # dpi_du = d_angle(wi, dwi_du_next)  # = 0
            dpoi_du = d_angle(woi, dwoi_du_next)

            dC_du_next = -dpoi_du
            self.vertices[k].dpoi_du_next = dpoi_du

            self.vertices[k].woi = woi
            self.vertices[k].dwi_du_prev = dwi_du_prev
            self.vertices[k].dwoi_du_cur = dwoi_du_cur
            self.vertices[k].dwo_du_next = dwo_du_next
            self.vertices[k].dwoi_du_next = dwoi_du_next

        dC = [dC_du_prev, dC_du_cur, dC_du_next]
        return (valid_refr_i or valid_refr_o), C, dC

    def compute_tangent_derivatives(self, constraint_type):
        self.gradC = None
        if not self.has_specular_segment():
            return

        gradC = np.zeros((self.n_specular, self.n_total))
        vC = np.zeros(self.n_specular)

        for i in range(self.n_specular):
            idx = i+1
            if constraint_type == ConstraintType.HalfVector:
                success, C, dC = self.grad_constraints_halfvector(idx)
            else:
                success, C, dC = self.grad_constraints_anglediff(idx)

            self.vertices[idx].C = C
            du_prev, du_cur, du_next = dC
            self.vertices[idx].dC_du_prev = du_prev
            self.vertices[idx].dC_du_cur  = du_cur
            self.vertices[idx].dC_du_next = du_next

            if not success:
                self.singular = True
                return

            gradC[i, idx-1] = du_prev
            gradC[i, idx]   = du_cur
            gradC[i, idx+1] = du_next
            vC[i] = C

        A = gradC[:,1:-1]
        B1   = gradC[:,0]
        Bk   = gradC[:,-1]

        self.singular = not np.abs(np.linalg.det(A)) > 0
        if self.singular:
            return

        self.gradC = gradC

        Ainv = np.linalg.inv(A)
        T1 = -Ainv @ B1
        Tk = -Ainv @ Bk
        Tx = Ainv @ vC

        for i in range(self.n_specular):
            idx = i+1
            self.vertices[idx].dC_du1 = T1[i]
            self.vertices[idx].dC_duk = Tk[i]
            self.vertices[idx].dX = Tx[i]

    def same_submanifold(self, other):
        if len(self) != len(other):
            return False
        for i in range(len(self)):
            if self.vertices[i].shape.id != other.vertices[i].shape.id:
                return False
        return True

    def print_derivative_debug(self, c_idx, c_type, eps=1e-5):
        path    = self.copy()
        path_du_prev = self.copy()
        path_du_cur  = self.copy()
        path_du_next = self.copy()

        path.compute_tangent_derivatives(c_type)

        print("-----")

        path_du_prev[c_idx-1] = path_du_prev[c_idx-1].shape.sample_position(path_du_prev[c_idx-1].u + eps)
        path_du_prev[c_idx-1].eta = path_du_prev[c_idx-1].shape.eta
        du = path_du_prev[c_idx-1].u - path[c_idx-1].u
        path_du_prev.compute_tangent_derivatives(c_type)

        print("d_prev:")
        if c_type == ConstraintType.HalfVector:
            dh_du_fd = (path_du_prev[c_idx].h - path[c_idx].h) / du
            print("dh_du: ", path[c_idx].dh_du_prev, " vs. ", dh_du_fd)
        dC_du_fd = (path_du_prev[c_idx].C - path[c_idx].C) / du
        print("dC_du: ", path[c_idx].dC_du_prev, " vs. ", dC_du_fd)
        print("")

        path_du_cur[c_idx] = path_du_cur[c_idx].shape.sample_position(path_du_cur[c_idx].u + eps)
        path_du_cur[c_idx].eta = path_du_cur[c_idx].shape.eta
        du = path_du_cur[c_idx].u - path[c_idx].u
        path_du_cur.compute_tangent_derivatives(c_type)

        print("d_cur:")
        dp_du_fd = (path_du_cur[c_idx].p - path[c_idx].p) / du
        print("dp_du: ", path[c_idx].dp_du, " vs. ", dp_du_fd)
        dn_du_fd = (path_du_cur[c_idx].n - path[c_idx].n) / du
        print("dn_du: ", path[c_idx].dn_du, " vs. ", dn_du_fd)
        ds_du_fd = (path_du_cur[c_idx].s - path[c_idx].s) / du
        print("ds_du: ", path[c_idx].ds_du, " vs. ", ds_du_fd)
        if c_type == ConstraintType.HalfVector:
            dh_du_fd = (path_du_cur[c_idx].h - path[c_idx].h) / du
            print("dh_du: ", path[c_idx].dh_du_cur, " vs. ", dh_du_fd)
        else:
            dwo_du_fd = (path_du_cur[c_idx].wo - path[c_idx].wo) / du
            print("dwo_du: ", path[c_idx].dwo_du_cur, " vs. ", dwo_du_fd)
            dwi_du_fd = (path_du_cur[c_idx].wi - path[c_idx].wi) / du
            print("dwi_du: ", path[c_idx].dwi_du_cur, " vs. ", dwi_du_fd)
            dwio_du_fd = (path_du_cur[c_idx].wio - path[c_idx].wio) / du
            print("dwio_du: ", path[c_idx].dwio_du_cur, " vs. ", dwio_du_fd)
            dwoi_du_fd = (path_du_cur[c_idx].woi - path[c_idx].woi) / du
            print("dwoi_du: ", path[c_idx].dwoi_du_cur, " vs. ", dwoi_du_fd)

            dpo_du_fd = (path_du_cur[c_idx].po - path[c_idx].po) / du
            print("dpo_du: ", path[c_idx].dpo_du_cur, " vs. ", dpo_du_fd)
            dpi_du_fd = (path_du_cur[c_idx].pi - path[c_idx].pi) / du
            print("dpi_du: ", path[c_idx].dpi_du_cur, " vs. ", dpi_du_fd)
            dpio_du_fd = (path_du_cur[c_idx].pio - path[c_idx].pio) / du
            print("dpio_du: ", path[c_idx].dpio_du_cur, " vs. ", dpio_du_fd)
            dpoi_du_fd = (path_du_cur[c_idx].poi - path[c_idx].poi) / du
            print("dpoi_du: ", path[c_idx].dpoi_du_cur, " vs. ", dpoi_du_fd)
        dC_du_fd = (path_du_cur[c_idx].C - path[c_idx].C) / du
        print("dC_du: ", path[c_idx].dC_du_cur, " vs. ", dC_du_fd)
        print("")

        path_du_next[c_idx+1] = path_du_next[c_idx+1].shape.sample_position(path_du_next[c_idx+1].u + eps)
        path_du_next[c_idx+1].eta = path_du_next[c_idx+1].shape.eta
        du = path_du_next[c_idx+1].u - path[c_idx+1].u
        path_du_next.compute_tangent_derivatives(c_type)

        print("d_next:")
        if c_type == ConstraintType.HalfVector:
            dh_du_fd = (path_du_next[c_idx].h - path[c_idx].h) / du
            print("dh_du: ", path[c_idx].dh_du_next, " vs. ", dh_du_fd)
        dC_du_fd = (path_du_next[c_idx].C - path[c_idx].C) / du
        print("dC_du: ", path[c_idx].dC_du_next, " vs. ", dC_du_fd)
        print("")

        print("-----")
