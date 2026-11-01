extends RefCounted
## Spatial hash: units sorted into square buckets so "who is near this point?" only looks at nearby
## buckets (web SIM rebuildHash/query). Visit order matches the web game exactly (bucket rows, then
## columns, then the order units were added), because combat picks targets in that order.
##
## Works with any objects that have x, z and alive (the Unit class arrives in phase 2).

var X0 := 0.0
var Z0 := 0.0
var size := 0.0      # bucket edge, balance.engine.hashBucket
var BW := 0
var BH := 0
var _buckets: Array = []


func _init(world_w: float, world_h: float, x0: float, z0: float, bucket: float) -> void:
	X0 = x0
	Z0 = z0
	size = bucket
	BW = int(ceilf(world_w / bucket))
	BH = int(ceilf(world_h / bucket))
	_buckets.resize(BW * BH)
	for k in BW * BH:
		_buckets[k] = []


func rebuild(units: Array) -> void:
	for b: Array in _buckets:
		b.clear()
	for u: Object in units:
		if not u.alive:
			continue
		var i := clampi(int(floorf((u.x - X0) / size)), 0, BW - 1)
		var j := clampi(int(floorf((u.z - Z0) / size)), 0, BH - 1)
		_buckets[j * BW + i].append(u)


## Calls fn(unit, squared_distance) for every live unit within r of (x, z).
func query(x: float, z: float, r: float, fn: Callable) -> void:
	var i0 := maxi(0, int(floorf((x - r - X0) / size)))
	var i1 := mini(BW - 1, int(floorf((x + r - X0) / size)))
	var j0 := maxi(0, int(floorf((z - r - Z0) / size)))
	var j1 := mini(BH - 1, int(floorf((z + r - Z0) / size)))
	var r2 := r * r
	for j in range(j0, j1 + 1):
		for i in range(i0, i1 + 1):
			for u: Object in _buckets[j * BW + i]:
				var dx: float = u.x - x
				var dz: float = u.z - z
				var d2 := dx * dx + dz * dz
				if d2 <= r2 and u.alive:
					fn.call(u, d2)
