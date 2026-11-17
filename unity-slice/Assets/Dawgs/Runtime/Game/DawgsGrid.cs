// Dawgs Uprising -> Unity: the browser game's walk grid (2.5 m cells over the whole map: open ground 1, blocked 0 -
// buildings, walls, cliffs and water) with 8-way A* and line-of-sight smoothing, like the game's own findPath.
// Grid cells are in the game's axes; positions here are Unity's (game z = -Unity z).
using System;
using System.Collections.Generic;
using UnityEngine;

public class DawgsGrid
{
    public readonly int GW, GH;
    public readonly float cell, x0, z0;
    readonly byte[] pass;
    // A* scratch
    readonly float[] g; readonly int[] parent; readonly int[] stamp; readonly bool[] closed; int gen;
    readonly int[] heap; readonly float[] heapKey; int heapN;
    readonly int[] heapPos;

    public DawgsGrid(DGGrid d, string passB64)
    {
        GW = d.GW; GH = d.GH; cell = d.CELL; x0 = d.X0; z0 = d.Z0;
        pass = Convert.FromBase64String(passB64);
        int n = GW * GH;
        g = new float[n]; parent = new int[n]; stamp = new int[n]; closed = new bool[n];
        heap = new int[n]; heapKey = new float[n]; heapPos = new int[n];
    }

    public int CellOf(Vector3 p)
    {
        int i = Mathf.FloorToInt((p.x - x0) / cell), j = Mathf.FloorToInt((-p.z - z0) / cell);
        if (i < 0 || j < 0 || i >= GW || j >= GH) return -1;
        return j * GW + i;
    }
    public Vector3 Center(int c) { int i = c % GW, j = c / GW; return new Vector3(x0 + (i + 0.5f) * cell, 0f, -(z0 + (j + 0.5f) * cell)); }
    public bool Open(int c) => c >= 0 && pass[c] == 1;
    public bool Passable(Vector3 p) => Open(CellOf(p));

    public int NearestOpen(int c, int maxR = 30)
    {
        if (Open(c)) return c;
        if (c < 0) return -1;
        int ci = c % GW, cj = c / GW;
        for (int r = 1; r <= maxR; r++)
        {
            int best = -1; float bd = 1e9f;
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Mathf.Abs(di) != r && Mathf.Abs(dj) != r) continue;
                    int i = ci + di, j = cj + dj;
                    if (i < 0 || j < 0 || i >= GW || j >= GH) continue;
                    int k = j * GW + i; if (pass[k] != 1) continue;
                    float d = di * di + dj * dj; if (d < bd) { bd = d; best = k; }
                }
            if (best >= 0) return best;
        }
        return -1;
    }

    public Vector3 Snap(Vector3 p)
    {
        int c = CellOf(p); if (Open(c)) return p;
        int k = NearestOpen(c); return k >= 0 ? Center(k) : p;
    }

    /// true if a walker can go straight from a to b (samples the segment, plus a little either side of it)
    public bool LOS(Vector3 a, Vector3 b, float halfWidth = 0.5f)
    {
        Vector3 d = b - a; d.y = 0f; float len = d.magnitude; if (len < 1e-3f) return Passable(a);
        Vector3 n = new Vector3(-d.z, 0f, d.x) / len * halfWidth;
        int steps = Mathf.CeilToInt(len / (cell * 0.4f));
        for (int s = 0; s <= steps; s++)
        {
            Vector3 p = a + d * (s / (float)steps);
            if (!Passable(p) || !Passable(p + n) || !Passable(p - n)) return false;
        }
        return true;
    }

    // ---- binary heap keyed on f ----
    void HPush(int c, float k)
    {
        int i = heapN++; heap[i] = c; heapKey[i] = k; heapPos[c] = i; Up(i);
    }
    void HDecrease(int c, float k) { int i = heapPos[c]; heapKey[i] = k; Up(i); }
    int HPop()
    {
        int top = heap[0]; heapN--;
        if (heapN > 0) { heap[0] = heap[heapN]; heapKey[0] = heapKey[heapN]; heapPos[heap[0]] = 0; Down(0); }
        heapPos[top] = -1; return top;
    }
    void Swap(int a, int b) { int t = heap[a]; heap[a] = heap[b]; heap[b] = t; float k = heapKey[a]; heapKey[a] = heapKey[b]; heapKey[b] = k; heapPos[heap[a]] = a; heapPos[heap[b]] = b; }
    void Up(int i) { while (i > 0) { int p = (i - 1) >> 1; if (heapKey[p] <= heapKey[i]) break; Swap(i, p); i = p; } }
    void Down(int i)
    {
        while (true)
        {
            int l = i * 2 + 1, r = l + 1, m = i;
            if (l < heapN && heapKey[l] < heapKey[m]) m = l;
            if (r < heapN && heapKey[r] < heapKey[m]) m = r;
            if (m == i) break; Swap(i, m); i = m;
        }
    }

    static readonly int[] DI = { 1, -1, 0, 0, 1, 1, -1, -1 }, DJ = { 0, 0, 1, -1, 1, -1, 1, -1 };
    static readonly float[] DC = { 1, 1, 1, 1, 1.41421f, 1.41421f, 1.41421f, 1.41421f };

    /// world-space waypoints from `from` to `to` (smoothed), or null if there is no way there
    public List<Vector3> FindPath(Vector3 from, Vector3 to, int maxExpand = 60000)
    {
        int s = NearestOpen(CellOf(from)), t = NearestOpen(CellOf(to));
        if (s < 0 || t < 0) return null;
        Vector3 goal = Passable(to) ? to : Center(t);
        if (s == t || LOS(from, goal)) return new List<Vector3> { goal };
        gen++; heapN = 0;
        int ti = t % GW, tj = t / GW;
        stamp[s] = gen; g[s] = 0f; parent[s] = -1; closed[s] = false;
        HPush(s, Heur(s % GW, s / GW, ti, tj));
        int found = -1, expanded = 0;
        while (heapN > 0)
        {
            int c = HPop();
            if (c == t) { found = c; break; }
            closed[c] = true;
            if (++expanded > maxExpand) break;
            int ci = c % GW, cj = c / GW;
            for (int k = 0; k < 8; k++)
            {
                int i = ci + DI[k], j = cj + DJ[k];
                if (i < 0 || j < 0 || i >= GW || j >= GH) continue;
                int nb = j * GW + i;
                if (pass[nb] != 1) continue;
                if (k >= 4 && (pass[cj * GW + i] != 1 || pass[j * GW + ci] != 1)) continue;   // no corner cutting
                float ng = g[c] + DC[k];
                if (stamp[nb] != gen) { stamp[nb] = gen; g[nb] = ng; parent[nb] = c; closed[nb] = false; HPush(nb, ng + Heur(i, j, ti, tj)); }
                else if (!closed[nb] && ng < g[nb]) { g[nb] = ng; parent[nb] = c; HDecrease(nb, ng + Heur(i, j, ti, tj)); }
            }
        }
        if (found < 0) return null;
        var cells = new List<int>();
        for (int c = found; c >= 0; c = parent[c]) cells.Add(c);
        cells.Reverse();
        // string-pull: keep only the corners we can't see past
        var pts = new List<Vector3>();
        Vector3 cur = from; int idx = 0;
        while (idx < cells.Count - 1)
        {
            int far = idx + 1;
            while (far + 1 < cells.Count && LOS(cur, Center(cells[Math.Min(cells.Count - 1, far + 2)]))) far = Math.Min(cells.Count - 1, far + 2);
            while (far + 1 < cells.Count && LOS(cur, Center(cells[far + 1]))) far++;
            cur = Center(cells[far]); pts.Add(cur); idx = far;
        }
        if (pts.Count > 0) pts[pts.Count - 1] = goal; else pts.Add(goal);
        return pts;
    }

    static float Heur(int i, int j, int ti, int tj)
    {
        int dx = Math.Abs(i - ti), dy = Math.Abs(j - tj);
        return (dx + dy) + (1.41421f - 2f) * Math.Min(dx, dy);
    }
}
