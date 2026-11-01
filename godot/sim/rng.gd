extends RefCounted
## Seeded random numbers, bit-exact with the web SIM's mulberry32().
## Every random choice in the SIM must come from one of these, never from Godot's global functions,
## so that the same seed gives the same battle on every machine and matches the web game.
##
## Works on unsigned 32-bit values held in 64-bit ints. The constants below are the algorithm's
## own (not gameplay numbers).

const M32 := 0xFFFFFFFF
const TWO32 := 4294967296.0

var _a: int
var draws := 0   # how many numbers have been drawn (tests compare this with the web game)


## `seed` may be negative or wider than 32 bits; only its low 32 bits are used, like JS `a|=0`.
func _init(seed: int) -> void:
	_a = seed & M32


## Next value as an unsigned 32-bit int (0 .. 2^32-1).
func next_u32() -> int:
	draws += 1
	_a = (_a + 0x6D2B79F5) & M32
	var t := imul(_a ^ (_a >> 15), 1 | _a)
	t = ((t + imul(t ^ (t >> 7), 61 | t)) & M32) ^ t
	return (t ^ (t >> 14)) & M32


## Next value in [0, 1), the same double the web rnd() returns.
func next() -> float:
	return next_u32() / TWO32


## JS Math.imul on unsigned 32-bit inputs, result unsigned 32-bit.
## Split in 16-bit halves so no intermediate product needs more than 49 bits.
static func imul(a: int, b: int) -> int:
	a &= M32
	b &= M32
	var lo := a * (b & 0xFFFF)
	var hi := ((a * (b >> 16)) & 0xFFFF) << 16
	return (lo + hi) & M32


## JS `x|0`: wrap to a signed 32-bit int.
static func to_i32(x: int) -> int:
	x &= M32
	return x - 0x100000000 if x >= 0x80000000 else x
