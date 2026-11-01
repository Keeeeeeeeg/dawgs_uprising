using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    /// <summary>
    /// Grid pathfinding, ported from the web SIM: nearestPassCell, cellCenter, snapPassable, los and findPath
    /// (A* over 8 neighbours with string pulling). Bit-exact with the web game: path costs and heap keys are
    /// stored as 32-bit floats like the web's Float32Arrays, which decides ties.
    ///
    /// Grids are byte arrays (1 = open). The walled-base courtyard rule of the web findPath (a target inside a
    /// closed courtyard is moved to its gate) arrives with walls.
    /// </summary>
    public sealed class Pathing
    {
        public readonly double X0, Z0, Cell;
        public readonly int GW, GH;
        public int Calls;   // web G.pathCalls

        readonly double _straight, _diag, _hdiag, _hweight, _losStep;
        readonly int _rings;
        readonly float[] _g;
        readonly int[] _par, _stamp, _closed;
        int _cur;
        readonly int[] _heapI;
        readonly float[] _heapF;
        int _hn;
        readonly int[] _di, _dj;
        readonly double[] _dc;

        public Pathing(Terrain t, JObj engine) : this(t.X0, t.Z0, t.Cell, t.GW, t.GH, engine) { }

        /// <summary>engine: balance.engine.</summary>
        public Pathing(double x0, double z0, double cell, int gw, int gh, JObj engine)
        {
            X0 = x0; Z0 = z0; Cell = cell; GW = gw; GH = gh;
            _straight = engine.Num("pathStraight");
            _diag = engine.Num("pathDiag");
            _hdiag = engine.Num("pathHeuristicDiag");
            _hweight = engine.Num("pathHeuristicWeight");
            _losStep = engine.Num("losStep");
            _rings = engine.Int("snapRings");
            int n = GW * GH;
            _g = new float[n];
            _par = new int[n];
            _stamp = new int[n];
            _closed = new int[n];
            _heapI = new int[n * 4];
            _heapF = new float[n * 4];
            // same order as the web DIRS: straight first, then diagonals
            _di = new[] { 1, -1, 0, 0, 1, 1, -1, -1 };
            _dj = new[] { 0, 0, 1, -1, 1, -1, 1, -1 };
            _dc = new[] { _straight, _straight, _straight, _straight, _diag, _diag, _diag, _diag };
        }

        public int CellOf(double x, double z)
        {
            int i = (int)Math.Floor((x - X0) / Cell), j = (int)Math.Floor((z - Z0) / Cell);
            if (i < 0 || j < 0 || i >= GW || j >= GH) return -1;
            return j * GW + i;
        }

        public bool Passable(double x, double z, byte[] grid)
        {
            int c = CellOf(x, z);
            return c >= 0 && grid[c] == 1;
        }

        public double[] CellCenter(int c) => new[] { X0 + (c % GW + 0.5) * Cell, Z0 + (c / GW + 0.5) * Cell };

        /// <summary>Nearest open cell, searching outward ring by ring (-1 if none within range).</summary>
        public int NearestPassCell(int c, byte[] grid)
        {
            if (c >= 0 && grid[c] != 0) return c;
            int ci = c < 0 ? 0 : c % GW, cj = c < 0 ? 0 : c / GW;
            for (int r = 1; r < _rings; r++)
                for (int dj = -r; dj <= r; dj++)
                    for (int di = -r; di <= r; di++)
                    {
                        if (Math.Abs(di) != r && Math.Abs(dj) != r) continue;
                        int i = ci + di, j = cj + dj;
                        if (i < 0 || j < 0 || i >= GW || j >= GH) continue;
                        int k = j * GW + i;
                        if (grid[k] != 0) return k;
                    }
            return -1;
        }

        /// <summary>The point itself if it's open, else the centre of the nearest open cell (web snapPassable).</summary>
        public double[] SnapPassable(double x, double z, byte[] grid)
        {
            if (Passable(x, z, grid)) return new[] { x, z };
            int c = NearestPassCell(CellOf(x, z), grid);
            return c < 0 ? new[] { x, z } : CellCenter(c);
        }

        /// <summary>Straight-line walkability, sampled every engine.losStep (web los).</summary>
        public bool Los(double x0, double z0, double x1, double z1, byte[] grid)
        {
            double d = DMath.Hypot(x1 - x0, z1 - z0);
            int n = (int)Math.Ceiling(d / _losStep);
            for (int i = 1; i <= n; i++)
            {
                double t = (double)i / n;
                if (!Passable(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, grid)) return false;
            }
            return true;
        }

        void HPush(int i, double f)
        {
            int k = _hn++;
            _heapI[k] = i;
            _heapF[k] = (float)f;
            while (k > 0)
            {
                int p = (k - 1) >> 1;
                if (_heapF[p] <= _heapF[k]) break;
                (_heapI[p], _heapI[k]) = (_heapI[k], _heapI[p]);
                (_heapF[p], _heapF[k]) = (_heapF[k], _heapF[p]);
                k = p;
            }
        }

        int HPop()
        {
            int r = _heapI[0];
            _hn--;
            if (_hn > 0)
            {
                _heapI[0] = _heapI[_hn];
                _heapF[0] = _heapF[_hn];
                int k = 0;
                while (true)
                {
                    int l = 2 * k + 1, rr = l + 1, m = k;
                    if (l < _hn && _heapF[l] < _heapF[m]) m = l;
                    if (rr < _hn && _heapF[rr] < _heapF[m]) m = rr;
                    if (m == k) break;
                    (_heapI[m], _heapI[k]) = (_heapI[k], _heapI[m]);
                    (_heapF[m], _heapF[k]) = (_heapF[k], _heapF[m]);
                    k = m;
                }
            }
            return r;
        }

        /// <summary>Waypoints [x, z] from (sx, sz) toward (tx, tz), or null if unreachable.</summary>
        public List<double[]> FindPath(double sx, double sz, double tx, double tz, byte[] grid)
        {
            Calls++;
            int s = NearestPassCell(CellOf(sx, sz), grid);
            int t = NearestPassCell(CellOf(tx, tz), grid);
            if (s < 0 || t < 0) return null;
            var tc = CellCenter(t);
            bool openTarget = Passable(tx, tz, grid);
            double fx = openTarget ? tx : tc[0], fz = openTarget ? tz : tc[1];
            if (s == t || Los(sx, sz, fx, fz, grid)) return new List<double[]> { new[] { fx, fz } };
            _cur++;
            _hn = 0;
            int ti = t % GW, tj = t / GW;
            _stamp[s] = _cur;
            _g[s] = 0f;
            _par[s] = -1;
            HPush(s, Heur(s, ti, tj));
            bool found = false;
            int iter = 0, n = GW * GH;
            while (_hn > 0)
            {
                int c = HPop();
                if (_closed[c] == _cur) continue;
                _closed[c] = _cur;
                if (c == t) { found = true; break; }
                if (++iter > n) break;
                int ci = c % GW, cj = c / GW;
                for (int d = 0; d < 8; d++)
                {
                    int ni = ci + _di[d], nj = cj + _dj[d];
                    if (ni < 0 || nj < 0 || ni >= GW || nj >= GH) continue;
                    int nc = nj * GW + ni;
                    if (grid[nc] == 0 || _closed[nc] == _cur) continue;
                    if (_dc[d] > 1.0 && (grid[cj * GW + ni] == 0 || grid[nj * GW + ci] == 0)) continue;
                    double ng = _g[c] + _dc[d];
                    if (_stamp[nc] != _cur || ng < _g[nc])
                    {
                        _stamp[nc] = _cur;
                        _g[nc] = (float)ng;
                        _par[nc] = c;
                        HPush(nc, ng + Heur(nc, ti, tj) * _hweight);
                    }
                }
            }
            if (!found) return null;
            var cells = new List<int>();
            for (int c2 = t; c2 != -1; c2 = _par[c2]) cells.Add(c2);
            cells.Reverse();
            var pts = cells.ConvertAll(CellCenter);
            pts[pts.Count - 1] = new[] { fx, fz };
            // string pulling: from where we are, jump to the farthest waypoint in sight
            var o = new List<double[]>();
            double cx = sx, cz = sz;
            int i = 0;
            while (i < pts.Count - 1)
            {
                int j = pts.Count - 1;
                while (j > i + 1 && !Los(cx, cz, pts[j][0], pts[j][1], grid)) j--;
                o.Add(pts[j]);
                cx = pts[j][0];
                cz = pts[j][1];
                i = j;
            }
            if (o.Count == 0) o.Add(pts[pts.Count - 1]);
            return o;
        }

        double Heur(int c, int ti, int tj)
        {
            int dx = Math.Abs(c % GW - ti), dz = Math.Abs(c / GW - tj);
            return Math.Max(dx, dz) + _hdiag * Math.Min(dx, dz);
        }
    }
}
