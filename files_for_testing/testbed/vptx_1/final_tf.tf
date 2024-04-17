terraform {
	required_providers {
		junos-vptx = {
			source = "juniper/providers/junos-vqfx"
			version = "23.11.101"
		}
	}
}

resource "jtaf_InterfacesInterfaceUnitFamilyInetAddressName" "jtaf" {
	resource_name = "jtaf"
	name = "et-0/0/0"
	name__1 = "0"
	name__2 = "10.0.0.1/30"
}

