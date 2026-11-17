// Dawgs Uprising -> Unity: one ground unit in the playable skirmish, moving and fighting by the browser game's rules
// (its SIM's updateUnit / stepToward / goToward / followPath, ported):
//   orders     move, fight-move (amove), attack a unit, attack an area, guard (escort) a friendly unit, halt; stances
//   movement   per movement class (infantry, light, tank, heavy): acceleration, braking to arrive, hull turn rate,
//              slowing while turning, backing up to a spot close behind instead of turning round; a formation can cap speed
//   fighting   closest target it can hurt (sticking to the one it has), turret traverse before firing, bursts,
//              magazines, reloads, deploy / pack-up (gunners, snipers, SPGs), artillery backing off inside minimum range,
//              keeping a shorter-ranged enemy at arm's length, going after whoever shot it (on a leash), then walking back
// DawgsGame steps every unit each frame, runs the formation marches and personal space, and resolves the shots.
using System.Collections.Generic;
using UnityEngine;

public enum DOrder { Idle, Move, Fight, Attack }
public enum DStance { Aggressive, Hold, ReturnFire }

public class DawgsUnit : MonoBehaviour
{
    public int id, army;
    public string type;
    public DGUnitDef def;
    public float hp, maxHp;
    public bool alive = true;
    public DawgsUnitRig rig;
    public Transform body;
    public DOrder order;
    public DStance stance = DStance.Aggressive;
    public Vector3 dest; public bool hasDest;
    public Vector3 anchor;               // where it stands when idle: it walks back here after a chase
    public DawgsUnit target, forced;     // forced: the unit it was told to attack
    public List<Vector3> path;
    public int pi;
    public float speedNow;               // m/s along its way (the browser's u.v)
    public Vector3 velocity;             // what this frame's movement made it
    public bool reversing;
    public float heading;                // radians; 0 = Unity +x, as Quaternion.Euler(0, deg, 0) turns the model
    public float turretAng;
    public float capV;                   // a formation's speed limit (0 = none)
    public DawgsGame.Formation form;     // the formation it is marching in
    public Vector3 march; public bool hasMarch;
    public DawgsUnit guardOf;            // the friendly unit it follows and protects
    public readonly List<DawgsUnit> guards = new List<DawgsUnit>();
    public bool hasArea; public Vector3 areaC; public float areaR;
    public bool deployed;
    public bool selected;
    public float radius = 0.5f;          // how big it looks (selection ring, picking, splash)
    public float rad = 0.4f;             // the browser's collision radius (personal space)
    public GameObject ring;
    public float hitT = -99f;
    public DawgsUnit attacker;           // who hit it last (the browser's lastHitBy)
    public float deadT;
    public bool infantry, turreted, armed;
    public int group = -1;
    public bool gone;                    // dead and finished falling: DawgsGame removes it
    public float formPathT;

    DawgsGame G;
    DGMoveClass mc;
    float cd, acqT, deployT, repathT, stuckT, losT, guardT;
    int burstN, rounds = -1;
    bool needRepath;
    List<Vector3> cpath; int cpi; Vector3 cgoal;
    Vector3 lastPos, guardLast, guardSpot; bool hasGuardLast, hasGuardSpot;
    MaterialPropertyBlock mpb;

    public Vector3 Pos => transform.position;
    public Vector3 Forward => new Vector3(Mathf.Cos(heading), 0f, -Mathf.Sin(heading));
    public bool Military => armed && !def.builder;
    public bool Guarding => guardOf != null;

    public void Init(DawgsGame game, int id, int army, DGUnitDef d, float heading)
    {
        G = game; this.id = id; this.army = army; def = d; type = d.key;
        hp = maxHp = d.hp; this.heading = heading; turretAng = heading;
        infantry = d.armor == "inf";
        turreted = d.turret > 0f;
        armed = d.dmg > 0f && d.range > 0f;
        radius = infantry ? 0.45f : d.armor == "hvy" ? 2.2f : 1.6f;
        rad = d.rad > 0f ? d.rad : infantry ? 0.4f : 1.15f;
        mc = G.R.MoveClass(d);
        rig = GetComponent<DawgsUnitRig>();
        body = transform.childCount > 0 ? transform.GetChild(0) : transform;
        cd = Random.value * Mathf.Max(0.2f, d.rof);
        acqT = Random.value * 0.3f;
        lastPos = anchor = transform.position;
        ApplyTransform(transform.position);
    }

    public float Vision => Mathf.Max(G.R.D.sight.min, def.sight > 0f ? def.sight : def.vision);
    public float AimHeight => infantry ? 0.5f : 1.1f;

    static float AngDf(float a, float b) { float d = a - b; while (d > Mathf.PI) d -= 2f * Mathf.PI; while (d < -Mathf.PI) d += 2f * Mathf.PI; return d; }
    static float AngLerp(float a, float b, float t) => a + AngDf(b, a) * Mathf.Min(1f, t);
    static float Flat(Vector3 a, Vector3 b) { float dx = a.x - b.x, dz = a.z - b.z; return Mathf.Sqrt(dx * dx + dz * dz); }
    static float HeadingTo(Vector3 from, Vector3 to) => Mathf.Atan2(-(to.z - from.z), to.x - from.x);

    // ---------------------------------------------------------------- orders (DawgsGame gives them)
    public void SetIdle()
    {
        order = DOrder.Idle; path = null; cpath = null; anchor = transform.position; capV = 0f;
        speedNow = Mathf.Min(speedNow, 1f); velocity = Vector3.zero;
    }

    /// any new order ends guard duty, an attack-area and a formation march
    public void Release()
    {
        if (guardOf != null) { guardOf.guards.Remove(this); guardOf = null; }
        hasArea = false; form = null; capV = 0f; hasMarch = false;
    }

    public void OrderPath(List<Vector3> p, Vector3 to, bool fight)
    {
        path = p; pi = 0; order = fight ? DOrder.Fight : DOrder.Move; forced = null; target = null; cpath = null;
        dest = to; hasDest = true; stuckT = 0f; lastPos = transform.position; needRepath = false;
    }
    /// compatibility with the first skirmish build: a move with its path ready
    public void OrderMove(Vector3 to, bool fight, List<Vector3> p) { Release(); OrderPath(p ?? new List<Vector3> { to }, to, fight); }
    public void OrderAttack(DawgsUnit t)
    {
        capV = 0f; form = null; order = DOrder.Attack; forced = t; target = t; path = null; cpath = null;
    }
    public void OrderHalt() { Release(); SetIdle(); forced = null; target = null; }
    public void OrderGuard(DawgsUnit t)
    {
        Release(); guardOf = t; hasGuardSpot = false; hasGuardLast = false; guardT = 0f; forced = null;
        if (!t.guards.Contains(this)) t.guards.Add(this);
    }

    // ---------------------------------------------------------------- per frame (the browser's updateUnit)
    public void Step(float dt)
    {
        if (!alive) { DeathStep(dt); return; }
        if (dt <= 0f) return;
        velocity = Vector3.zero;
        var C = G.R.D.combat; var d = def;
        if (guardOf != null) GuardTick(dt);
        cd -= dt; acqT -= dt;
        if (hasArea && !(forced != null && forced.alive))
        {   // attack area: the next target in the circle
            var t = G.AreaPick(this);
            if (t != null) OrderAttack(t);
            else { hasArea = false; forced = null; if (order == DOrder.Attack) SetIdle(); }
        }
        if (forced != null && !forced.alive) { forced = null; if (order == DOrder.Attack) SetIdle(); }
        if (acqT <= 0f)
        {
            acqT = C.acquire + Random.value * C.acquireJitter;
            if (!armed) target = null;
            else if (forced != null) target = forced;
            else if (stance == DStance.ReturnFire) { var r = RetaliationTarget(); target = r != null && Flat(Pos, r.Pos) <= d.range ? r : null; }
            else
            {
                var t = NearestEnemy(order == DOrder.Move || stance == DStance.Hold ? d.range : Vision);
                // nothing in reach but it is being shot at from beyond it: go after the shooter
                if (order != DOrder.Move && stance == DStance.Aggressive && (t == null || Flat(Pos, t.Pos) > d.range))
                { var r = RetaliationTarget(); if (r != null && LeashOK(r)) t = r; }
                target = t;
            }
        }
        var tgt = target; if (tgt != null && !tgt.alive) tgt = target = null;
        if (tgt != null && G.R.Eff(d, tgt.def) <= 0f) { if (forced != null) { forced = null; if (order == DOrder.Attack) SetIdle(); } tgt = target = null; }

        bool inRange = false, chase = false, tooClose = false;
        Vector3 pos = transform.position;
        if (tgt != null)
        {
            float dist = Flat(pos, tgt.Pos);
            if (d.minR > 0f && dist < d.minR) { tooClose = true; if (forced == null) target = null; }
            else if (dist <= d.range)
            {
                inRange = true;
                if (d.deploy > 0f && order != DOrder.Move && !deployed) { deployT += dt; if (deployT >= d.deploy) { deployed = true; deployT = 0f; } }
                bool aimed = true; float a = HeadingTo(pos, tgt.Pos);
                if (turreted) { turretAng = AngLerp(turretAng, a, dt * d.turret); aimed = Mathf.Abs(AngDf(a, turretAng)) < C.turretAim; }
                if (order != DOrder.Move) heading = AngLerp(heading, a, dt * (d.isVeh ? 4f : 9f));     // the hull (or the soldier) turns to face it
                if (rig) rig.Aim(tgt.Pos + Vector3.up * tgt.AimHeight);
                if (aimed && cd <= 0f && (d.deploy <= 0f || deployed))
                {
                    G.Shoot(this, tgt);
                    float cr = Mathf.Max(0.05f, d.rof);
                    if (d.burst != null && d.burst.Length >= 3) { burstN++; if (burstN >= (int)d.burst[0]) { burstN = 0; cr = d.burst[2]; } else cr = d.burst[1]; }
                    if (d.mag > 0f) { if (rounds < 0) rounds = (int)d.mag; rounds--; if (rounds <= 0) { rounds = (int)d.mag; burstN = 0; cr = d.reload; } }
                    cd = cr * (C.rofJitterMin + Random.value * C.rofJitterSpread);
                }
            }
            else if (order != DOrder.Move)
            {
                if ((forced != null || stance == DStance.Aggressive) && LeashOK(tgt)) chase = true;
                else if (forced == null) target = null;
            }
        }
        if (turreted && !inRange) turretAng = AngLerp(turretAng, heading, dt * d.turret * 0.5f);   // nothing to shoot: the turret settles forward

        if (!d.isStatic) Move(dt, tgt, inRange, chase, tooClose);
        ApplyTransform(transform.position);
        if (rig)
        {
            rig.SetMotion(velocity.magnitude, reversing && velocity.sqrMagnitude > 0.01f);
            rig.SetDeployed(d.kneel && deployed);
            if (turreted && !infantry) rig.SetTurret(Mathf.DeltaAngle(0f, (turretAng - heading) * Mathf.Rad2Deg));
        }
    }

    void Move(float dt, DawgsUnit tgt, bool inRange, bool chase, bool tooClose)
    {
        var C = G.R.D.combat; var d = def; Vector3 pos = transform.position;
        // artillery backs away from enemies inside its minimum range
        if (tooClose && order != DOrder.Move && tgt != null)
        {
            Vector3 away = pos - tgt.Pos; away.y = 0f; away = away.sqrMagnitude > 1e-4f ? away.normalized : Forward;
            StepToward(pos + away * C.minRangeBackoff, dt, 0.5f); return;
        }
        if (d.deploy > 0f)
        {
            bool wantsMove = order == DOrder.Move || (!inRange && (chase || order == DOrder.Fight || order == DOrder.Attack || Flat(pos, anchor) > 2.5f));
            if (inRange && order != DOrder.Move) return;                                   // stays planted while firing
            if (wantsMove && deployed) { burstN = 0; deployT += dt; if (deployT >= d.deploy) { deployed = false; deployT = 0f; } return; }   // packs up first
            if (!wantsMove && !deployed && deployT > 0f) deployT = Mathf.Max(0f, deployT - dt);
        }
        // keep a shorter-ranged enemy at arm's length between shots
        if (inRange && tgt != null && order != DOrder.Move && stance == DStance.Aggressive && d.deploy <= 0f && cd > 0f && tgt.def.range > 0f &&
            tgt.def.range < d.range - 3f && G.R.Eff(tgt.def, d) > 0f)
        {
            if (Flat(pos, tgt.Pos) < d.range * C.kiteAt)
            {
                Vector3 away = pos - tgt.Pos; away.y = 0f; away.Normalize(); float h0 = heading;
                StepToward(pos + away * 3f, dt * 0.7f, 0.2f); heading = h0; anchor = transform.position; return;
            }
        }
        if (order == DOrder.Move) { FollowPath(dt); return; }
        if (order == DOrder.Fight)
        {
            if (inRange) return;
            if (chase) { GoToward(tgt.Pos, dt, d.range * C.chaseStop); needRepath = true; return; }
            FollowPath(dt); return;
        }
        if (order == DOrder.Attack)
        {
            if (!inRange && tgt != null) GoToward(tgt.Pos, dt, d.range * C.chaseStop);
            return;
        }
        // idle
        if (inRange) return;
        if (chase) { GoToward(tgt.Pos, dt, d.range * C.chaseStop); return; }
        if (Flat(pos, anchor) > 2.5f) GoToward(anchor, dt, 1.5f); else cpath = null;
    }

    // ---------------------------------------------------------------- movement (stepToward / goToward / followPath)
    bool StepToward(Vector3 to, float dt, float arrive)
    {
        Vector3 pos = transform.position;
        float dx = to.x - pos.x, dz = to.z - pos.z, dist = Mathf.Sqrt(dx * dx + dz * dz);
        if (dist <= arrive) { velocity = Vector3.zero; return true; }
        float vx = dx / dist, vz = dz / dist; var M = mc; float want = Mathf.Atan2(-vz, vx);
        // heading: vehicles turn at their own rate, and back up to a spot close behind them instead of turning round
        float face = want; bool rev = false;
        if (M.rev > 0f && dist < M.revDist && !(form != null && capV > 0f) && Mathf.Abs(AngDf(want, heading)) > 2.2f) { rev = true; face = want + Mathf.PI; }
        float turn = M.turn * dt; heading += Mathf.Clamp(AngDf(face, heading), -turn, turn);
        // speed: toward the top speed (lower in reverse, while still turning, and when braking to arrive)
        float top = (capV > 0f ? Mathf.Min(def.speed, capV) : def.speed) * (rev ? M.rev : 1f);
        float facing = M.align > 0f ? Mathf.Max(0f, 1f - M.align * (1f - Mathf.Cos(Mathf.Min(Mathf.PI, Mathf.Abs(AngDf(face, heading)))))) : 1f;
        float brake = Mathf.Sqrt(2f * M.dec * Mathf.Max(0f, dist - arrive * 0.5f)) + 0.4f;
        float goal = Mathf.Min(top * facing, brake);
        speedNow = speedNow < goal ? Mathf.Min(goal, speedNow + M.acc * dt) : Mathf.Max(goal, speedNow - M.dec * dt);
        float sp = speedNow * dt, m = Mathf.Min(sp, dist); Vector3 o = pos;
        if (!G.Grid.Passable(pos))
        {   // stuck inside something: step back out the nearest way
            Vector3 e = G.Grid.Snap(pos) - pos; e.y = 0f; float el = e.magnitude;
            if (el > 1e-3f) transform.position = pos + e / el * Mathf.Min(el, Mathf.Max(sp, 0.02f));
            return false;
        }
        var n = new Vector3(pos.x + vx * m, pos.y, pos.z + vz * m);
        if (G.Grid.Passable(n)) pos = n;
        else if (G.Grid.Passable(new Vector3(pos.x + vx * m, pos.y, pos.z))) pos.x += vx * m;
        else if (G.Grid.Passable(new Vector3(pos.x, pos.y, pos.z + vz * m))) pos.z += vz * m;
        velocity = dt > 0f ? (pos - o) / dt : Vector3.zero; reversing = rev;
        transform.position = pos;
        return Flat(to, pos) <= arrive;
    }

    /// chase / go toward a point along a cached sub-path, refreshed about once a second
    bool GoToward(Vector3 to, float dt, float arrive)
    {
        repathT -= dt;
        if (cpath == null || repathT <= 0f || Flat(cgoal, to) > 4f)
        {
            if (G.Grid.LOS(Pos, to, 0.4f)) cpath = new List<Vector3> { to };
            else if (G.pathBudget > 0) { G.pathBudget--; cpath = G.Grid.FindPath(Pos, to) ?? new List<Vector3> { to }; }
            else if (cpath == null) cpath = new List<Vector3> { to };
            cpi = 0; cgoal = to; repathT = 1f + Random.value * 0.6f;
        }
        var wp = cpath[Mathf.Min(cpi, cpath.Count - 1)]; bool last = cpi >= cpath.Count - 1;
        if (StepToward(wp, dt, last ? arrive : 1.2f)) { if (last) return true; cpi++; }
        return false;
    }

    void FollowPath(float dt)
    {
        if (needRepath && hasDest && G.pathBudget > 0) { G.pathBudget--; path = G.Grid.FindPath(Pos, dest); pi = 0; needRepath = false; }
        if (path == null || pi >= path.Count) { SetIdle(); return; }
        var wp = path[pi]; bool last = pi == path.Count - 1;
        // something between it and the next waypoint: find a new way round instead of sliding along it
        losT -= dt;
        if (losT <= 0f) { losT = 0.5f + Random.value * 0.3f; if (hasDest && form == null && !G.Grid.LOS(Pos, wp, 0.15f)) needRepath = true; }
        if (StepToward(wp, dt, last ? 0.5f : 1.4f)) { pi++; if (pi >= path.Count) SetIdle(); }
        stuckT += dt;
        if (stuckT > 1.5f)
        {
            if (Flat(Pos, lastPos) < 0.6f) { if (last) SetIdle(); else needRepath = true; }
            stuckT = 0f; lastPos = Pos;
        }
    }

    /// the formation keeps a marching unit from counting as stuck (DawgsGame.FormTick)
    public void ClearStuck() { stuckT = 0f; }

    public void ApplyTransform(Vector3 p)
    {
        p.y = G.GroundY(p);
        transform.SetPositionAndRotation(p, Quaternion.Euler(0f, heading * Mathf.Rad2Deg, 0f));
    }

    // ---------------------------------------------------------------- targets
    DawgsUnit NearestEnemy(float R)
    {
        DawgsUnit best = null; float bestScore = 1e9f, curScore = 1e9f;
        var T = G.R.D.targeting;
        foreach (var o in G.units)
        {
            if (!o.alive || o.army == army) continue;
            float dd = Flat(Pos, o.Pos); if (dd > R) continue;
            float e = G.R.Eff(def, o.def); if (e <= 0f) continue;
            float score = dd / Mathf.Max(0.05f, e);
            if (e < T.uselessBelow) score *= T.uselessPenalty;
            if (o == target) curScore = score;
            if (score < bestScore) { bestScore = score; best = o; }
        }
        if (target != null && target.alive && curScore < 1e8f && curScore * T.stickiness <= bestScore) return target;
        return best;
    }

    /// can it usefully go after the unit that shot it?
    DawgsUnit RetaliationTarget()
    {
        var a = attacker;
        if (a == null || !a.alive || a.army == army || G.time - hitT > G.R.D.retaliate.memory) return null;
        if (G.R.Eff(def, a.def) < 0.1f || def.isStatic) return null;
        return a;
    }

    bool LeashOK(DawgsUnit t)
    {
        if (forced != null) return true;
        if (order == DOrder.Fight) return true;
        var RET = G.R.D.retaliate;
        bool ret = t == attacker && G.time - hitT < RET.memory;      // hunting whoever just shot it: a longer leash
        if (order == DOrder.Idle) return Flat(t.Pos, anchor) < (ret ? RET.leash : RET.idleLeash);
        return false;
    }

    // ---------------------------------------------------------------- guard: follow a friendly unit and protect it
    void GuardTick(float dt)
    {
        var GD = G.R.D.guard; var t = guardOf;
        if (t == null || !t.alive || t.army != army) { if (t != null) t.guards.Remove(this); guardOf = null; SetIdle(); return; }
        guardT -= dt; if (guardT > 0f) return;
        guardT = GD.every * (0.85f + Random.value * 0.3f);
        Vector3 v = hasGuardLast ? (t.Pos - guardLast) / GD.every : Vector3.zero; v.y = 0f;
        guardLast = t.Pos; hasGuardLast = true;
        float dT = Flat(Pos, t.Pos);
        // a threat to the one it guards: whoever just shot it, else the nearest enemy close to it that this unit can hurt
        DawgsUnit foe = t.attacker != null && t.attacker.alive && G.time - t.hitT < 3f && t.attacker.army != army ? t.attacker : null;
        if (foe != null && (G.R.Eff(def, foe.def) <= 0f || Flat(foe.Pos, t.Pos) > GD.leash)) foe = null;
        if (foe == null)
        {
            float bd = GD.radius;
            foreach (var o in G.units)
            {
                if (!o.alive || o.army == army || G.R.Eff(def, o.def) <= 0f) continue;
                float dd = Flat(o.Pos, t.Pos); if (dd < bd) { bd = dd; foe = o; }
            }
        }
        if (foe != null && dT < GD.leash) { if (forced != foe) OrderAttack(foe); return; }
        if (order == DOrder.Attack) { forced = null; target = null; SetIdle(); }
        // station: a ring around it, turned with its heading, a little ahead of where it's going
        int n = Mathf.Max(1, t.guards.Count), i = Mathf.Max(0, t.guards.IndexOf(this));
        float R = t.rad + rad + GD.pad + (n > 8 ? rad * (i / 8) : 0f), a = t.heading + Mathf.PI + (i % 8 + 0.5f) / Mathf.Min(n, 8) * Mathf.PI * 2f;
        Vector3 spot = t.Pos + new Vector3(Mathf.Cos(a), 0f, -Mathf.Sin(a)) * R + v * GD.lead;
        if (Flat(Pos, spot) < GD.slack && v.magnitude < 0.3f) { if (order != DOrder.Idle) SetIdle(); return; }
        if (hasGuardSpot && Flat(spot, guardSpot) < GD.slack * 0.5f && order != DOrder.Idle) return;   // already on the way
        guardSpot = spot; hasGuardSpot = true;
        G.MoveOne(this, spot, true);
    }

    public Vector3 Muzzle()
    {
        if (rig && rig.isActiveAndEnabled) return rig.MuzzlePosition;
        return Pos + Vector3.up * (infantry ? 0.6f : 1.4f) + Forward * (radius * 0.8f);
    }

    /// hit by something: note it for the rig (a resting soldier gets up)
    public void Struck() { if (rig) rig.Alert(); }

    // ---------------------------------------------------------------- death
    public void Die()
    {
        alive = false; deadT = 0f; selected = false; speedNow = 0f; velocity = Vector3.zero;
        Release();
        foreach (var g in guards) if (g) g.guardOf = null;
        guards.Clear();
        if (ring) ring.SetActive(false);
        if (rig) { rig.enabled = false; if (rig.animator) rig.animator.enabled = false; }
        if (!infantry)
        {
            mpb = new MaterialPropertyBlock();
            foreach (var r in GetComponentsInChildren<Renderer>())
            {
                r.GetPropertyBlock(mpb); mpb.SetColor("_BaseColor", new Color(0.22f, 0.2f, 0.18f, 1f)); r.SetPropertyBlock(mpb);
            }
        }
    }

    void DeathStep(float dt)
    {
        deadT += dt;
        if (infantry)
        {   // topple sideways, lie a while, sink away
            float k = Mathf.Clamp01(deadT / 0.45f);
            float roll = 88f * (1f - (1f - k) * (1f - k));
            var p = transform.position;
            if (deadT > 6f) p.y -= dt * 0.25f;
            transform.SetPositionAndRotation(p, Quaternion.Euler(0f, heading * Mathf.Rad2Deg, 0f) * Quaternion.Euler(roll, 0f, 0f));
            if (deadT > 10f) gone = true;
        }
        else
        {
            var p = transform.position;
            if (deadT > 12f) { p.y -= dt * 0.3f; transform.position = p; }
            if (deadT > 18f) gone = true;
        }
    }
}
