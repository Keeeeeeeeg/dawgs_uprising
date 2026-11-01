extends RefCounted
## Value noise, bit-exact with the web SIM's makeNoise() and fbm(): a size x size table of
## seeded random values stored as 32-bit floats (the web uses a Float32Array), smoothly interpolated.

const Rng := preload("res://sim/rng.gd")

var _p := PackedFloat32Array()
var _n := 0
var _mask := 0


func _init(seed: int, size: int) -> void:
	_n = size
	_mask = size - 1
	_p.resize(size * size)
	var r := Rng.new(seed)
	for i in size * size:
		_p[i] = r.next()


func sample(x: float, y: float) -> float:
	var xf := floorf(x)
	var yf := floorf(y)
	var fx := x - xf
	var fy := y - yf
	var u := fx * fx * (3.0 - 2.0 * fx)
	var v := fy * fy * (3.0 - 2.0 * fy)
	var xi := int(xf)
	var yi := int(yf)
	var x0 := (xi & _mask) * _n
	var x1 := ((xi + 1) & _mask) * _n
	var y0 := yi & _mask
	var y1 := (yi + 1) & _mask
	var a: float = _p[x0 + y0]
	var b: float = _p[x1 + y0]
	var c: float = _p[x0 + y1]
	var d: float = _p[x1 + y1]
	return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


## Fractal sum of `octaves` layers: amplitude starts at `gain` and is multiplied by it each layer,
## frequency is multiplied by `lacunarity`.
func fbm(x: float, y: float, octaves: int, gain: float, lacunarity: float) -> float:
	var s := 0.0
	var a := gain
	var f := 1.0
	var t := 0.0
	for i in octaves:
		s += sample(x * f, y * f) * a
		t += a
		a *= gain
		f *= lacunarity
	return s / t
