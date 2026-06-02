data modify storage minecraft:temp mcs_log set value ""
data modify storage minecraft:temp mcs_log append value from storage $(s0) $(n0)
data modify storage minecraft:temp mcs_log append value from storage $(s1) $(n1)
data modify storage minecraft:temp mcs_log append value from storage $(s2) $(n2)
data modify storage minecraft:temp mcs_log append value from storage $(s3) $(n3)
data modify storage minecraft:temp mcs_log append value from storage $(s4) $(n4)
$tellraw @a [{"nbt":"mcs_log","storage":"minecraft:temp","interpret":true}]
