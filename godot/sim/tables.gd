extends RefCounted
## The SIM's derived tables, built from balance.json like the web SIM does at load time:
## unit types (UTYPES: adds key, hr, wpn, rad, isVeh, sight, vision), zone types (ZTYPES: adds hr,
## recruit), facilities (adds prod.seq) and plot counts per base type. No numbers here: radii, sight
## and vision padding all come from balance.json.

var utypes := {}
var ztypes := {}
var facilities := {}
var plots := {}


func _init(balance: Dictionary) -> void:
	var RAD: Dictionary = balance.unitRadius
	var SG: Dictionary = balance.sight
	var VIS: Dictionary = balance.vision
	for key: String in balance.units:
		var b: Dictionary = balance.units[key]
		var t := b.duplicate(true)
		t.key = key
		t.hr = b.mp
		t.wpn = b.weapon
		var armor: String = b.get("armor", "")
		var rad: float
		if b.get("carrier", false):
			rad = RAD.carrier
		elif armor == "ship":
			rad = RAD.ship
		elif b.get("naval", false):
			rad = RAD.boat
		elif b.get("air", false):
			rad = RAD.air
		elif armor == "hvy":
			rad = RAD.hvy
		elif armor == "inf":
			rad = RAD.inf
		elif key == "pillbox":
			rad = RAD.pillbox
		elif key == "how":
			rad = RAD.how
		else:
			rad = RAD.other
		t.rad = rad
		t.isVeh = armor == "veh" or armor == "hvy"
		t.sight = maxf(SG.min, b.range + SG.pad)
		t.vision = maxf(t.sight + SG.visionExtra, VIS.get(key, 0.0))
		if b.get("plane", false):
			t.rad = RAD.plane
			t.air = true
		utypes[key] = t
	for k: String in balance.facilities:
		var f: Dictionary = balance.facilities[k].duplicate(true)
		if f.has("seq"):
			f.prod = {"seq": f.seq}
		facilities[k] = f
	for k: String in balance.zones:
		var z: Dictionary = balance.zones[k].duplicate(true)
		z.hr = z.mp
		z.recruit = true
		ztypes[k] = z
		plots[k] = z.slots.mil + z.slots.eco + z.slots.fort
