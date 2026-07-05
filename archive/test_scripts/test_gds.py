import gdsfactory as gf

from layout.pdk_setup import activate_pdk


activate_pdk()

c = gf.components.straight(length=10, width=0.5)
c.write_gds("test_straight.gds")

print("GDS file generated: test_straight.gds")
