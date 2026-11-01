extends RefCounted
## Grid pathfinding, ported from the web SIM: nearestPassCell, cellCenter, snapPassable, los and
## findPath (A* over 8 neighbours with string pulling). Bit-exact with the web game: path costs and
## heap keys are stored as 32-bit floats like the web's Float32Arrays, which decides ties.
##
## Grids are PackedByteArray (1 = open). The walled-base courtyard rule of the web findPath (a target
## inside a closed courtyard is moved to its gate) arrives with walls in phase 4.

const DMath := preload("res://sim/dmath.gd")

var X0 := 0.0
var Z0 := 0.0
var cell := 0.0
var GW := 0
var GH := 0
var calls := 0       # web G.pathCalls

var _straight := 1.0
var _diag := 1.414
var _hdiag := 0.0
var _hweight := 0.0
var _los_step := 0.0
var _rings := 0

var _g := PackedFloat32Array()
var _par := PackedInt32Array()
var _stamp := PackedInt64Array()
var _closed := PackedInt64Array()
var _cur := 0
var _heap_i := PackedInt32Array()
var _heap_f := PackedFloat32Array()
var _hn := 0
var _dirs: Array = []


## terrain: sim/terrain.gd (for the grid size and position). engine: balance.engine.
func _init(terrain: RefCounted, engine: Dictionary) -> void:
	X0 = terrain.X0
	Z0 = terrain.Z0
	cell = terrain.cell
	GW = terrain.GW
	GH = terrain.GH
	_straight = engine.pathStraight
	_diag = engine.pathDiag
	_hdiag = engine.pathHeuristicDiag
	_hweight = engine.pathHeuristicWeight
	_los_step = engine.losStep
	_rings = int(engine.snapRings)
	var n := GW * GH
	_g.resize(n)
	_par.resize(n)
	_stamp.resize(n)
	_closed.resize(n)
	_heap_i.resize(n * 4)
	_heap_f.resize(n * 4)
	# same order as the web DIRS: straight first, then diagonals
	_dirs = [[1, 0, _straight], [-1, 0, _straight], [0, 1, _straight], [0, -1, _straight],
		[1, 1, _diag], [1, -1, _diag], [-1, 1, _diag], [-1, -1, _diag]]


func cell_of(x: float, z: float) -> int:
	var i := int(floorf((x - X0) / cell))
	var j := int(floorf((z - Z0) / cell))
	if i < 0 or j < 0 or i >= GW or j >= GH:
		return -1
	return j * GW + i


func passable(x: float, z: float, grid: PackedByteArray) -> bool:
	var c := cell_of(x, z)
	return c >= 0 and grid[c] == 1


func cell_center(c: int) -> Array:
	return [X0 + (c % GW + 0.5) * cell, Z0 + (c / GW + 0.5) * cell]


## Nearest open cell, searching outward ring by ring (-1 if none within range).
func nearest_pass_cell(c: int, grid: PackedByteArray) -> int:
	if c >= 0 and grid[c] != 0:
		return c
	var ci := 0 if c < 0 else c % GW
	var cj := 0 if c < 0 else c / GW
	for r in range(1, _rings):
		for dj in range(-r, r + 1):
			for di in range(-r, r + 1):
				if absi(di) != r and absi(dj) != r:
					continue
				var i := ci + di
				var j := cj + dj
				if i < 0 or j < 0 or i >= GW or j >= GH:
					continue
				var k := j * GW + i
				if grid[k] != 0:
					return k
	return -1


## The point itself if it's open, else the centre of the nearest open cell (web snapPassable).
func snap_passable(x: float, z: float, grid: PackedByteArray) -> Array:
	if passable(x, z, grid):
		return [x, z]
	var c := nearest_pass_cell(cell_of(x, z), grid)
	return [x, z] if c < 0 else cell_center(c)


## Straight-line walkability, sampled every engine.losStep (web los).
func los(x0: float, z0: float, x1: float, z1: float, grid: PackedByteArray) -> bool:
	var d := DMath.hypot(x1 - x0, z1 - z0)
	var n := int(ceilf(d / _los_step))
	for i in range(1, n + 1):
		var t := float(i) / n
		if not passable(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, grid):
			return false
	return true


func _hpush(i: int, f: float) -> void:
	var k := _hn
	_hn += 1
	_heap_i[k] = i
	_heap_f[k] = f
	while k > 0:
		var p := (k - 1) >> 1
		if _heap_f[p] <= _heap_f[k]:
			break
		var ti := _heap_i[p]
		var tf := _heap_f[p]
		_heap_i[p] = _heap_i[k]
		_heap_f[p] = _heap_f[k]
		_heap_i[k] = ti
		_heap_f[k] = tf
		k = p


func _hpop() -> int:
	var r := _heap_i[0]
	_hn -= 1
	if _hn > 0:
		_heap_i[0] = _heap_i[_hn]
		_heap_f[0] = _heap_f[_hn]
		var k := 0
		while true:
			var l := 2 * k + 1
			var rr := l + 1
			var m := k
			if l < _hn and _heap_f[l] < _heap_f[m]:
				m = l
			if rr < _hn and _heap_f[rr] < _heap_f[m]:
				m = rr
			if m == k:
				break
			var ti := _heap_i[m]
			var tf := _heap_f[m]
			_heap_i[m] = _heap_i[k]
			_heap_f[m] = _heap_f[k]
			_heap_i[k] = ti
			_heap_f[k] = tf
			k = m
	return r


## A list of waypoints [x, z] from (sx,sz) toward (tx,tz), or null if unreachable.
func find_path(sx: float, sz: float, tx: float, tz: float, grid: PackedByteArray) -> Variant:
	calls += 1
	var s := nearest_pass_cell(cell_of(sx, sz), grid)
	var t := nearest_pass_cell(cell_of(tx, tz), grid)
	if s < 0 or t < 0:
		return null
	var tc: Array = cell_center(t)
	var open_target := passable(tx, tz, grid)
	var fx: float = tx if open_target else tc[0]
	var fz: float = tz if open_target else tc[1]
	if s == t:
		return [[fx, fz]]
	if los(sx, sz, fx, fz, grid):
		return [[fx, fz]]
	_cur += 1
	_hn = 0
	var ti := t % GW
	var tj := t / GW
	_stamp[s] = _cur
	_g[s] = 0.0
	_par[s] = -1
	_hpush(s, _heur(s, ti, tj))
	var found := false
	var iter := 0
	var n := GW * GH
	while _hn > 0:
		var c := _hpop()
		if _closed[c] == _cur:
			continue
		_closed[c] = _cur
		if c == t:
			found = true
			break
		iter += 1
		if iter > n:
			break
		var ci := c % GW
		var cj := c / GW
		for d: Array in _dirs:
			var ni: int = ci + d[0]
			var nj: int = cj + d[1]
			if ni < 0 or nj < 0 or ni >= GW or nj >= GH:
				continue
			var nc := nj * GW + ni
			if grid[nc] == 0 or _closed[nc] == _cur:
				continue
			if d[2] > 1.0 and (grid[cj * GW + ni] == 0 or grid[nj * GW + ci] == 0):
				continue
			var ng: float = _g[c] + d[2]
			if _stamp[nc] != _cur or ng < _g[nc]:
				_stamp[nc] = _cur
				_g[nc] = ng
				_par[nc] = c
				_hpush(nc, ng + _heur(nc, ti, tj) * _hweight)
	if not found:
		return null
	var cells := []
	var c2 := t
	while c2 != -1:
		cells.append(c2)
		c2 = _par[c2]
	cells.reverse()
	var pts := []
	for c3: int in cells:
		pts.append(cell_center(c3))
	pts[pts.size() - 1] = [fx, fz]
	# string pulling: from where we are, jump to the farthest waypoint in sight
	var out := []
	var cx := sx
	var cz := sz
	var i := 0
	while i < pts.size() - 1:
		var j := pts.size() - 1
		while j > i + 1 and not los(cx, cz, pts[j][0], pts[j][1], grid):
			j -= 1
		out.append(pts[j])
		cx = pts[j][0]
		cz = pts[j][1]
		i = j
	if out.is_empty():
		out.append(pts[pts.size() - 1])
	return out


func _heur(c: int, ti: int, tj: int) -> float:
	var dx := absi(c % GW - ti)
	var dz := absi(c / GW - tj)
	return maxi(dx, dz) + _hdiag * mini(dx, dz)
